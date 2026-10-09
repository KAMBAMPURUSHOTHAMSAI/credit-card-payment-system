import csv
import logging
from datetime import datetime, time, timedelta
from decimal import Decimal, InvalidOperation
from time import perf_counter

from django.db import connection, transaction as db_transaction
from django.db.models import Count, Max, Q, Sum
from django.http import HttpResponse
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AdminLog, Card, Transaction
from .permissions import (
    ROLE_ADMIN,
    ROLE_SUPPORT,
    AdminCardManagementPermission,
    IsAdminOrSupportUserCustom,
    IsApplicationRoleUserCustom,
    user_has_any_role,
)
from .serializers import CardSerializer, TransactionSerializer

logger = logging.getLogger(__name__)


# =========================================================
# HELPERS
# =========================================================

def get_client_ip(request):
    """Return the client IP supplied by the request/proxy."""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def get_local_day_range(target_date):
    """Return timezone-aware [start, end) for a local date."""
    current_timezone = timezone.get_current_timezone()
    start_of_day = timezone.make_aware(
        datetime.combine(target_date, time.min),
        current_timezone,
    )
    return start_of_day, start_of_day + timedelta(days=1)


def decimal_or_zero(value):
    return Decimal("0.00") if value is None else value


def get_card_spent_amount(card):
    result = Transaction.objects.filter(
        card=card,
        status="SUCCESS",
    ).aggregate(total=Sum("amount"))
    return decimal_or_zero(result["total"])


def get_card_management_response(card, use_annotations=False):
    """Return safe admin-facing card details; never expose PAN/CVV."""
    if use_annotations:
        spent_amount = decimal_or_zero(card.annotated_spent_amount)
        transaction_count = card.annotated_transaction_count or 0
        last_activity = card.annotated_last_activity
    else:
        spent_amount = get_card_spent_amount(card)
        card_transactions = Transaction.objects.filter(card=card)
        transaction_count = card_transactions.count()
        last_transaction = card_transactions.order_by("-created_at").first()
        last_activity = last_transaction.created_at if last_transaction else None

    available_credit = max(
        card.credit_limit - spent_amount,
        Decimal("0.00"),
    )
    return {
        "id": card.id,
        "username": card.user.username,
        "email": card.user.email,
        "card_brand": card.card_brand,
        "card_type": card.card_type,
        "masked_number": card.masked_number,
        "last4": card.last4,
        "expiry_month": card.expiry_month,
        "expiry_year": card.expiry_year,
        "credit_limit": card.credit_limit,
        "is_active": card.is_active,
        "spent_amount": spent_amount,
        "available_credit": available_credit,
        "transaction_count": transaction_count,
        "last_activity": last_activity,
    }


# =========================================================
# USER CARD MANAGEMENT
# =========================================================

class CardListCreateView(generics.ListCreateAPIView):
    """List active cards owned by the authenticated user or create a card."""
    serializer_class = CardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Card.objects.filter(
            user=self.request.user,
            is_active=True,
        ).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CardDeleteView(generics.DestroyAPIView):
    """Soft-delete a user's card so transaction history remains valid."""
    serializer_class = CardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Card.objects.filter(
            user=self.request.user,
            is_active=True,
        )

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active"])


# =========================================================
# USER TRANSACTION HISTORY
# =========================================================

class TransactionPagination(PageNumberPagination):
    """Server-side pagination with a bounded page size."""
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class TransactionListView(generics.ListAPIView):
    """User-scoped transaction search with validated filters and pagination."""
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = TransactionPagination
    filter_backends = [OrderingFilter]
    ordering_fields = ["created_at", "amount", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        params = self.request.query_params
        queryset = (
            Transaction.objects
            .filter(user=self.request.user)
            .select_related("card")
            .order_by("-created_at")
        )

        status_value = params.get("status", "").strip().upper()
        if status_value:
            allowed_statuses = {choice[0] for choice in Transaction.STATUS_CHOICES}
            if status_value not in allowed_statuses:
                raise ValidationError({"status": "Invalid transaction status."})
            queryset = queryset.filter(status=status_value)

        exact_amount = params.get("amount")
        if exact_amount not in (None, ""):
            amount = self._parse_amount("amount", exact_amount)
            queryset = queryset.filter(amount=amount)

        raw_start_date = params.get("start_date", "").strip()
        raw_end_date = params.get("end_date", "").strip()
        parsed_start_date = parse_date(raw_start_date) if raw_start_date else None
        parsed_end_date = parse_date(raw_end_date) if raw_end_date else None
        if raw_start_date and parsed_start_date is None:
            raise ValidationError({"start_date": "Use YYYY-MM-DD format."})
        if raw_end_date and parsed_end_date is None:
            raise ValidationError({"end_date": "Use YYYY-MM-DD format."})
        if parsed_start_date and parsed_end_date and parsed_start_date > parsed_end_date:
            raise ValidationError({"start_date": "Cannot be after end_date."})

        for param_name, lookup in (
            ("start_date", "gte"),
            ("end_date", "lt"),
        ):
            raw_date = params.get(param_name, "").strip()
            if not raw_date:
                continue
            parsed_date = parse_date(raw_date)
            if parsed_date is None:
                raise ValidationError({param_name: "Use YYYY-MM-DD format."})
            start_datetime, end_datetime = get_local_day_range(parsed_date)
            boundary = start_datetime if lookup == "gte" else end_datetime
            queryset = queryset.filter(**{f"created_at__{lookup}": boundary})

        raw_min = params.get("min_amount", "").strip()
        raw_max = params.get("max_amount", "").strip()
        min_amount = self._parse_amount("min_amount", raw_min) if raw_min else None
        max_amount = self._parse_amount("max_amount", raw_max) if raw_max else None

        if min_amount is not None and max_amount is not None and min_amount > max_amount:
            raise ValidationError({"min_amount": "Cannot exceed max_amount."})
        if min_amount is not None:
            queryset = queryset.filter(amount__gte=min_amount)
        if max_amount is not None:
            queryset = queryset.filter(amount__lte=max_amount)

        card_search = (
            params.get("card_search")
            or params.get("masked_card_search")
            or ""
        ).strip()
        if card_search:
            if len(card_search) > 20:
                raise ValidationError({"card_search": "Search must be 20 characters or fewer."})
            queryset = queryset.filter(card__masked_number__icontains=card_search)

        fraud_status = params.get("fraud_status", "").strip().upper()
        if fraud_status:
            if not hasattr(Transaction, "fraud_status"):
                raise ValidationError({"fraud_status": "Fraud status is not configured."})
            queryset = queryset.filter(fraud_status=fraud_status)

        return queryset

    @staticmethod
    def _parse_amount(field, value):
        try:
            amount = Decimal(value)
        except (InvalidOperation, TypeError, ValueError):
            raise ValidationError({field: "Enter a valid amount."})
        if not amount.is_finite() or amount < 0:
            raise ValidationError({field: "Amount must be a finite non-negative number."})
        return amount


# =========================================================
# DAILY ADMIN / ROLE DASHBOARD
# =========================================================

class AdminDashboardView(APIView):
    """Daily transaction summary and UI capabilities for the current role."""
    permission_classes = [IsApplicationRoleUserCustom]

    def get(self, request):
        today = timezone.localdate()
        start_of_day, end_of_day = get_local_day_range(today)
        transactions = Transaction.objects.filter(
            created_at__gte=start_of_day,
            created_at__lt=end_of_day,
        )
        summary = transactions.aggregate(
            total_transactions=Count("id"),
            total_amount=Sum("amount"),
            success_count=Count("id", filter=Q(status="SUCCESS")),
            failed_count=Count("id", filter=Q(status="FAILED")),
            pending_count=Count("id", filter=Q(status="PENDING")),
        )

        can_manage_card_status = user_has_any_role(
            request.user, {ROLE_ADMIN, ROLE_SUPPORT}
        )
        can_update_credit_limit = user_has_any_role(
            request.user, {ROLE_ADMIN}
        )
        can_export_transactions = user_has_any_role(
            request.user, {ROLE_ADMIN, ROLE_SUPPORT}
        )

        AdminLog.objects.create(
            admin=request.user,
            action="VIEW_DAILY_SUMMARY",
            target="DAILY_SUMMARY",
            ip_address=get_client_ip(request),
        )
        return Response({
            "date": str(today),
            "total_transactions": summary["total_transactions"] or 0,
            "total_amount": summary["total_amount"] or Decimal("0.00"),
            "success_count": summary["success_count"] or 0,
            "failed_count": summary["failed_count"] or 0,
            "pending_count": summary["pending_count"] or 0,
            "permissions": {
                "can_manage_card_status": can_manage_card_status,
                "can_update_credit_limit": can_update_credit_limit,
                "can_export_transactions": can_export_transactions,
                "can_export_analytics": True,
            },
        })


def _month_start(target_date, offset=0):
    """Return the first day of a month shifted by offset months."""
    month_index = target_date.year * 12 + target_date.month - 1 + offset
    return datetime(month_index // 12, month_index % 12 + 1, 1).date()


def _aware_month_bounds(month_date):
    current_timezone = timezone.get_current_timezone()
    start = timezone.make_aware(
        datetime.combine(month_date, time.min), current_timezone
    )
    next_date = _month_start(month_date, 1)
    end = timezone.make_aware(
        datetime.combine(next_date, time.min), current_timezone
    )
    return start, end


def build_analytics_payload():
    """Build aggregate analytics in SQL without loading all transactions."""
    today = timezone.localdate()
    current_month = today.replace(day=1)
    month_dates = [_month_start(current_month, offset) for offset in range(-5, 1)]
    monthly_spending = []

    for month_date in month_dates:
        start, end = _aware_month_bounds(month_date)
        total = Transaction.objects.filter(
            status="SUCCESS",
            created_at__gte=start,
            created_at__lt=end,
        ).aggregate(total=Sum("amount"))["total"]
        monthly_spending.append({
            "month": month_date.strftime("%Y-%m"),
            "total": decimal_or_zero(total),
        })

    category_rows = (
        Transaction.objects
        .filter(status="SUCCESS")
        .values("category")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )
    category_spending = [
        {
            "category": row["category"] or "OTHER",
            "total": decimal_or_zero(row["total"]),
        }
        for row in category_rows
    ]

    total_credit_limit = decimal_or_zero(
        Card.objects.filter(
            card_type="CREDIT",
            is_active=True,
        ).aggregate(total=Sum("credit_limit"))["total"]
    )
    used_credit = decimal_or_zero(
        Transaction.objects.filter(
            card__card_type="CREDIT",
            card__is_active=True,
            status="SUCCESS",
        ).aggregate(total=Sum("amount"))["total"]
    )
    utilization_percent = (
        (used_credit / total_credit_limit) * Decimal("100")
        if total_credit_limit > 0
        else Decimal("0.00")
    )

    return {
        "monthly_spending": monthly_spending,
        "category_spending": category_spending,
        "credit_utilization": {
            "total_credit_limit": total_credit_limit,
            "used_credit": used_credit,
            "utilization_percent": utilization_percent,
        },
        "generated_at": timezone.now().isoformat(),
    }


class AdminAnalyticsView(APIView):
    """Monthly spending, category totals, and overall credit utilization."""
    permission_classes = [IsApplicationRoleUserCustom]

    def get(self, request):
        payload = build_analytics_payload()
        AdminLog.objects.create(
            admin=request.user,
            action="VIEW_ANALYTICS_SUMMARY",
            target="PAYMENT_ANALYTICS",
            ip_address=get_client_ip(request),
        )
        return Response(payload, status=status.HTTP_200_OK)


class AdminAnalyticsExportView(APIView):
    """Export the aggregate analytics as CSV or PDF for assigned roles."""
    permission_classes = [IsApplicationRoleUserCustom]

    def get(self, request):
        export_format = request.query_params.get("format", "csv").lower()
        if export_format not in {"csv", "pdf"}:
            return Response(
                {"detail": "format must be csv or pdf."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payload = build_analytics_payload()
        rows = [("Report", "Dimension", "Value")]
        for item in payload["monthly_spending"]:
            rows.append(("Monthly Spending", item["month"], str(item["total"])))
        for item in payload["category_spending"]:
            rows.append(("Category Spending", item["category"], str(item["total"])))
        utilization = payload["credit_utilization"]
        rows.extend([
            ("Credit Utilization", "Total Credit Limit", str(utilization["total_credit_limit"])),
            ("Credit Utilization", "Used Credit", str(utilization["used_credit"])),
            ("Credit Utilization", "Utilization Percent", str(utilization["utilization_percent"])),
        ])

        if export_format == "csv":
            response = HttpResponse(content_type="text/csv; charset=utf-8")
            response["Content-Disposition"] = 'attachment; filename="creditpay-analytics.csv"'
            writer = csv.writer(response)
            writer.writerows(rows)
            AdminLog.objects.create(
                admin=request.user,
                action="EXPORT_ANALYTICS_CSV",
                target="PAYMENT_ANALYTICS",
                ip_address=get_client_ip(request),
            )
            return response

        try:
            from io import BytesIO
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import mm
            from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
        except ImportError:
            return Response(
                {"detail": "PDF generation dependency is not installed."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        buffer = BytesIO()
        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=15 * mm,
            leftMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
            title="CreditPay Analytics Summary",
            author="CreditPay",
        )
        styles = getSampleStyleSheet()
        story = [
            Paragraph("CreditPay Analytics Summary", styles["Title"]),
            Paragraph(f"Generated: {payload['generated_at']}", styles["Normal"]),
            Spacer(1, 6 * mm),
        ]
        table = Table(rows, repeatRows=1, colWidths=[48 * mm, 65 * mm, 55 * mm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D1D5DB")),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(table)
        document.build(story)
        response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="creditpay-analytics.pdf"'
        buffer.close()
        AdminLog.objects.create(
            admin=request.user,
            action="EXPORT_ANALYTICS_PDF",
            target="PAYMENT_ANALYTICS",
            ip_address=get_client_ip(request),
        )
        return response


class AdminHealthView(APIView):
    """Expose a basic authenticated database/API health check."""
    permission_classes = [IsApplicationRoleUserCustom]

    def get(self, request):
        started = perf_counter()
        database_status = "connected"
        app_status = "healthy"
        database_reachable = True
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception:
            logger.exception("Admin health check database probe failed.")
            database_status = "unavailable"
            app_status = "degraded"
            database_reachable = False

        response_time_ms = round((perf_counter() - started) * 1000, 2)
        checked_at = timezone.now().isoformat()
        if database_reachable:
            AdminLog.objects.create(
                admin=request.user,
                action="VIEW_SYSTEM_HEALTH",
                target="SYSTEM_HEALTH",
                ip_address=get_client_ip(request),
            )
        body = {
            "status": app_status,
            "database_status": database_status,
            "response_time_ms": response_time_ms,
            "checked_at": checked_at,
        }
        response_status = (
            status.HTTP_200_OK
            if app_status == "healthy"
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )
        return Response(body, status=response_status)


# =========================================================
# TRANSACTION CSV EXPORT
# =========================================================

class AdminExportTransactionsView(APIView):
    """Export all transactions to CSV for Admin and Support roles."""
    permission_classes = [IsAdminOrSupportUserCustom]

    def get(self, request):
        transactions = (
            Transaction.objects
            .select_related("user", "card")
            .order_by("-created_at")
        )
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="transactions.csv"'
        writer = csv.writer(response)
        writer.writerow([
            "Reference", "Username", "Email", "Card", "Amount",
            "Currency", "Status", "Description", "Failure Reason", "Created At",
        ])
        for item in transactions:
            writer.writerow([
                item.reference,
                item.user.username,
                item.user.email,
                item.card.masked_number,
                item.amount,
                item.currency,
                item.status,
                item.description,
                item.failure_reason,
                item.created_at,
            ])
        AdminLog.objects.create(
            admin=request.user,
            action="EXPORT_TRANSACTIONS",
            target="TRANSACTIONS_CSV",
            ip_address=get_client_ip(request),
        )
        return response


# =========================================================
# ROLE-BASED ADMIN CARD MANAGEMENT + AUDIT LOGS
# =========================================================

class AdminCardManagementView(APIView):
    """
    GET is available to all assigned application roles.
    PATCH permissions are enforced by AdminCardManagementPermission:
    Admin/Support can block or unblock; Admin alone can change limits.
    """
    permission_classes = [AdminCardManagementPermission]

    def get(self, request):
        cards = (
            Card.objects.select_related("user")
            .annotate(
                annotated_spent_amount=Sum(
                    "transactions__amount",
                    filter=Q(transactions__status="SUCCESS"),
                ),
                annotated_transaction_count=Count("transactions__id", distinct=True),
                annotated_last_activity=Max("transactions__created_at"),
            )
            .order_by("-created_at")
        )
        response_data = [
            get_card_management_response(card, use_annotations=True)
            for card in cards
        ]
        AdminLog.objects.create(
            admin=request.user,
            action="VIEW_CARD_MANAGEMENT",
            target="ALL_CARDS",
            ip_address=get_client_ip(request),
        )
        return Response(response_data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        try:
            card = Card.objects.select_related("user").get(pk=pk)
        except Card.DoesNotExist:
            return Response({"detail": "Card not found."}, status=status.HTTP_404_NOT_FOUND)

        if not request.data:
            return Response(
                {"detail": "At least one field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        allowed_fields = {"is_active", "credit_limit"}
        unsupported_fields = set(request.data.keys()) - allowed_fields
        if unsupported_fields:
            return Response(
                {"detail": "Unsupported field(s): " + ", ".join(sorted(unsupported_fields))},
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_is_active = card.is_active
        old_credit_limit = card.credit_limit
        new_is_active = old_is_active
        new_credit_limit = old_credit_limit

        if "is_active" in request.data:
            value = request.data.get("is_active")
            if not isinstance(value, bool):
                return Response(
                    {"detail": "is_active must be true or false."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            new_is_active = value

        if "credit_limit" in request.data:
            try:
                new_credit_limit = Decimal(str(request.data.get("credit_limit")))
            except (InvalidOperation, TypeError, ValueError):
                return Response(
                    {"detail": "credit_limit must be a valid number."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not new_credit_limit.is_finite():
                return Response(
                    {"detail": "credit_limit must be a finite number."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if new_credit_limit < 0:
                return Response(
                    {"detail": "credit_limit cannot be negative."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if new_credit_limit > Decimal("9999999999.99"):
                return Response(
                    {"detail": "credit_limit is too large."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if card.card_type == "CREDIT" and new_credit_limit <= 0:
                return Response(
                    {"detail": "Credit cards must have a positive credit limit."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if card.card_type == "DEBIT" and new_credit_limit != 0:
                return Response(
                    {"detail": "Debit cards must have a credit limit of 0."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            spent_amount = get_card_spent_amount(card)
            if new_credit_limit < spent_amount:
                return Response(
                    {
                        "detail": "Credit limit cannot be lower than the card's successful spending.",
                        "spent_amount": str(spent_amount),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        with db_transaction.atomic():
            card.is_active = new_is_active
            card.credit_limit = new_credit_limit
            card.save(update_fields=["is_active", "credit_limit"])

            if old_is_active != new_is_active:
                AdminLog.objects.create(
                    admin=request.user,
                    action="BLOCK_CARD" if not new_is_active else "UNBLOCK_CARD",
                    target=f"CARD_{card.id}",
                    ip_address=get_client_ip(request),
                )

            if old_credit_limit != new_credit_limit:
                AdminLog.objects.create(
                    admin=request.user,
                    action="UPDATE_CREDIT_LIMIT",
                    target=f"CARD_{card.id} LIMIT {old_credit_limit} -> {new_credit_limit}"[:100],
                    ip_address=get_client_ip(request),
                )

            if old_is_active and not new_is_active:
                db_transaction.on_commit(
                    lambda card_id=card.id: self._send_card_blocked_alert(card_id)
                )

            if new_is_active and card.card_type == "CREDIT" and new_credit_limit > 0:
                spent_amount = get_card_spent_amount(card)
                available_credit = max(new_credit_limit - spent_amount, Decimal("0.00"))
                old_available_credit = max(old_credit_limit - spent_amount, Decimal("0.00"))
                old_percent = (
                    old_available_credit / old_credit_limit
                    if old_credit_limit > 0 else Decimal("0")
                )
                new_percent = available_credit / new_credit_limit
                if old_percent >= Decimal("0.10") and new_percent < Decimal("0.10"):
                    db_transaction.on_commit(
                        lambda card_id=card.id: self._send_low_credit_alert(card_id)
                    )

        card.refresh_from_db()
        return Response(get_card_management_response(card), status=status.HTTP_200_OK)

    @staticmethod
    def _send_card_blocked_alert(card_id):
        """Send the blocked-card email after transaction commit; never undo the card update."""
        try:
            from .notifications import send_card_blocked_alert
            card = Card.objects.select_related("user").get(pk=card_id)
            send_card_blocked_alert(card)
        except Exception:
            # Notification errors must not undo or mask the committed card operation.
            return

    @staticmethod
    def _send_low_credit_alert(card_id):
        """Send the low-credit email after transaction commit."""
        try:
            from .notifications import send_low_credit_alert
            card = Card.objects.select_related("user").get(pk=card_id)
            available_credit = max(
                card.credit_limit - get_card_spent_amount(card),
                Decimal("0.00"),
            )
            send_low_credit_alert(card, available_credit)
        except Exception:
            return


# =========================================================
# MONTHLY STATEMENT PDF
# =========================================================

class MonthlyStatementView(APIView):
    """Generate a monthly PDF statement for the authenticated user only."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        year_value = request.query_params.get("year")
        month_value = request.query_params.get("month")
        current_year = timezone.localdate().year

        try:
            year = int(year_value)
        except (TypeError, ValueError):
            return Response(
                {"detail": "year must be a valid number."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if year < 2000 or year > current_year + 1:
            return Response(
                {"detail": "year is outside the supported range."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            month = int(month_value)
        except (TypeError, ValueError):
            return Response(
                {"detail": "month must be a valid number."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if month < 1 or month > 12:
            return Response(
                {"detail": "month must be between 1 and 12."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        current_timezone = timezone.get_current_timezone()
        month_start_date = datetime(year, month, 1).date()
        next_month_date = (
            datetime(year + 1, 1, 1).date()
            if month == 12
            else datetime(year, month + 1, 1).date()
        )
        month_start = timezone.make_aware(
            datetime.combine(month_start_date, time.min), current_timezone
        )
        month_end = timezone.make_aware(
            datetime.combine(next_month_date, time.min), current_timezone
        )

        transaction_list = list(
            Transaction.objects.filter(
                user=request.user,
                created_at__gte=month_start,
                created_at__lt=month_end,
            ).select_related("card").order_by("created_at")
        )

        total_transactions = len(transaction_list)
        total_spending = sum(
            (item.amount for item in transaction_list if item.status == "SUCCESS"),
            Decimal("0.00"),
        )
        success_count = sum(1 for item in transaction_list if item.status == "SUCCESS")
        failed_count = sum(1 for item in transaction_list if item.status == "FAILED")
        pending_count = sum(1 for item in transaction_list if item.status == "PENDING")

        try:
            from io import BytesIO
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_LEFT
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
            from reportlab.lib.units import mm
            from reportlab.platypus import (
                Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
            )
        except ImportError:
            return Response(
                {"detail": "PDF generation dependency is not installed."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        buffer = BytesIO()
        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=15 * mm,
            leftMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
            title="CreditPay Monthly Statement",
            author="CreditPay",
        )
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "StatementTitle", parent=styles["Title"], fontSize=20,
            leading=24, alignment=TA_LEFT, spaceAfter=4,
        )
        subtitle_style = ParagraphStyle(
            "StatementSubtitle", parent=styles["Normal"], fontSize=10,
            leading=14, alignment=TA_LEFT,
        )
        section_style = ParagraphStyle(
            "Section", parent=styles["Heading2"], fontSize=12,
            leading=15, spaceBefore=8, spaceAfter=6,
        )
        normal_style = ParagraphStyle(
            "NormalText", parent=styles["Normal"], fontSize=9, leading=12,
        )
        right_style = ParagraphStyle(
            "RightText", parent=normal_style, alignment=2,
        )
        story = [
            Paragraph("CreditPay", title_style),
            Paragraph("Monthly Credit Card Statement", subtitle_style),
            Spacer(1, 6 * mm),
        ]

        customer_name = request.user.get_full_name() or request.user.username
        customer_email = getattr(request.user, "email", "") or "Not available"
        statement_month = datetime(year, month, 1).strftime("%B %Y")
        customer_table = Table(
            [
                [
                    Paragraph("<b>Customer</b>", normal_style),
                    Paragraph(str(customer_name), normal_style),
                    Paragraph("<b>Statement Period</b>", normal_style),
                    Paragraph(statement_month, normal_style),
                ],
                [
                    Paragraph("<b>Email</b>", normal_style),
                    Paragraph(str(customer_email), normal_style),
                    Paragraph("<b>Total Transactions</b>", normal_style),
                    Paragraph(str(total_transactions), right_style),
                ],
            ],
            colWidths=[28 * mm, 63 * mm, 38 * mm, 43 * mm],
        )
        customer_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F5F7FA")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D7DE")),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E5E7EB")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.extend([
            customer_table,
            Spacer(1, 5 * mm),
            Paragraph("Statement Summary", section_style),
        ])

        summary_table = Table(
            [
                [Paragraph("<b>Total Spending</b>", normal_style), Paragraph(f"INR {total_spending:,.2f}", right_style)],
                [Paragraph("<b>Successful</b>", normal_style), Paragraph(str(success_count), right_style)],
                [Paragraph("<b>Failed</b>", normal_style), Paragraph(str(failed_count), right_style)],
                [Paragraph("<b>Pending</b>", normal_style), Paragraph(str(pending_count), right_style)],
            ],
            colWidths=[65 * mm, 75 * mm],
        )
        summary_table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D7DE")),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E5E7EB")),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF4FF")),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.extend([
            summary_table,
            Spacer(1, 5 * mm),
            Paragraph("Transaction Details", section_style),
        ])

        transaction_data = [["Date", "Reference", "Card", "Amount", "Status"]]
        for item in transaction_list:
            created_date = timezone.localtime(item.created_at).strftime("%d-%m-%Y %H:%M")
            transaction_data.append([
                created_date,
                item.reference,
                item.card.masked_number,
                f"{item.currency} {item.amount:,.2f}",
                item.status,
            ])
        if not transaction_list:
            transaction_data.append(["No transactions", "-", "-", "INR 0.00", "-"])

        transaction_table = Table(
            transaction_data,
            colWidths=[28 * mm, 40 * mm, 35 * mm, 32 * mm, 25 * mm],
            repeatRows=1,
        )
        transaction_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7.5),
            ("LEADING", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#D1D5DB")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.extend([
            transaction_table,
            Spacer(1, 6 * mm),
            Paragraph(
                "<b>Security Notice:</b> This statement displays only masked card information. "
                "Full card numbers, CVV, and other sensitive authentication information are not included.",
                normal_style,
            ),
        ])

        document.build(story)
        pdf_data = buffer.getvalue()
        buffer.close()
        response = HttpResponse(pdf_data, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="creditpay_statement_{year}_{month:02d}.pdf"'
        )
        return response
