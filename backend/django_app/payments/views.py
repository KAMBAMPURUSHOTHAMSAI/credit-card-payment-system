import csv

from datetime import datetime, time, timedelta
from decimal import Decimal, InvalidOperation

from django.db import transaction as db_transaction
from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.utils import timezone
from django.utils.dateparse import parse_date

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AdminLog, Card, Transaction
from .permissions import IsAdminUserCustom
from .serializers import CardSerializer, TransactionSerializer


# =========================================================
# HELPER FUNCTIONS
# =========================================================


def get_client_ip(request):
    """
    Get the client IP address from the request.

    Supports reverse-proxy forwarded IPs.
    """

    forwarded = request.META.get(
        "HTTP_X_FORWARDED_FOR"
    )

    if forwarded:
        return forwarded.split(",")[0].strip()

    return request.META.get(
        "REMOTE_ADDR"
    )


def get_local_day_range(target_date):
    """
    Return the timezone-aware start and end datetime
    for one local calendar day.

    Example:
        2026-09-29 00:00:00 IST
        to
        2026-09-30 00:00:00 IST
    """

    current_timezone = (
        timezone.get_current_timezone()
    )

    start_of_day = timezone.make_aware(
        datetime.combine(
            target_date,
            time.min,
        ),
        current_timezone,
    )

    end_of_day = (
        start_of_day + timedelta(days=1)
    )

    return start_of_day, end_of_day


def decimal_or_zero(value):
    """
    Convert None aggregate values to Decimal zero.
    """

    if value is None:
        return Decimal("0.00")

    return value


def get_card_spent_amount(card):
    """
    Return successful transaction spending for a card.
    """

    result = (
        Transaction.objects
        .filter(
            card=card,
            status="SUCCESS",
        )
        .aggregate(
            total=Sum("amount")
        )
    )

    return decimal_or_zero(
        result["total"]
    )


def get_card_management_response(card):
    """
    Build the safe admin-facing card response.

    Full card number and CVV are never returned.
    """

    spent_amount = get_card_spent_amount(
        card
    )

    transaction_count = (
        Transaction.objects
        .filter(card=card)
        .count()
    )

    last_transaction = (
        Transaction.objects
        .filter(card=card)
        .order_by("-created_at")
        .first()
    )

    available_credit = (
        card.credit_limit - spent_amount
    )

    if available_credit < 0:
        available_credit = Decimal("0.00")

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
        "last_activity": (
            last_transaction.created_at
            if last_transaction
            else None
        ),
    }


# =========================================================
# CARD MANAGEMENT
# =========================================================


class CardListCreateView(
    generics.ListCreateAPIView
):
    """
    GET:
        Return active cards belonging to
        the currently authenticated user.

    POST:
        Create a new saved card.
    """

    serializer_class = CardSerializer

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):
        return (
            Card.objects
            .filter(
                user=self.request.user,
                is_active=True,
            )
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user
        )


class CardDeleteView(
    generics.DestroyAPIView
):
    """
    Soft-delete a saved card.

    The database row is retained so that
    existing transaction history remains valid.
    """

    serializer_class = CardSerializer

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):
        return Card.objects.filter(
            user=self.request.user,
            is_active=True,
        )

    def perform_destroy(self, instance):
        instance.is_active = False

        instance.save(
            update_fields=[
                "is_active"
            ]
        )


# =========================================================
# TRANSACTION HISTORY
# =========================================================


class TransactionListView(
    generics.ListAPIView
):
    """
    Return transaction history for the
    currently authenticated user.

    Supported filters:

    status
    amount
    start_date
    end_date
    min_amount
    max_amount
    """

    serializer_class = TransactionSerializer

    permission_classes = [
        IsAuthenticated
    ]

    filter_backends = [
        DjangoFilterBackend
    ]

    filterset_fields = [
        "status",
        "amount",
    ]

    def get_queryset(self):

        queryset = (
            Transaction.objects
            .filter(
                user=self.request.user
            )
            .select_related("card")
            .order_by("-created_at")
        )

        # -------------------------------------------------
        # DATE FILTERS
        # -------------------------------------------------

        start_date_value = (
            self.request.query_params.get(
                "start_date"
            )
        )

        end_date_value = (
            self.request.query_params.get(
                "end_date"
            )
        )

        # Start date
        if start_date_value:

            start_date = parse_date(
                start_date_value
            )

            if start_date is not None:

                start_datetime, _ = (
                    get_local_day_range(
                        start_date
                    )
                )

                queryset = queryset.filter(
                    created_at__gte=start_datetime
                )

        # End date
        if end_date_value:

            end_date = parse_date(
                end_date_value
            )

            if end_date is not None:

                _, end_datetime = (
                    get_local_day_range(
                        end_date
                    )
                )

                queryset = queryset.filter(
                    created_at__lt=end_datetime
                )

        # -------------------------------------------------
        # AMOUNT FILTERS
        # -------------------------------------------------

        min_amount = (
            self.request.query_params.get(
                "min_amount"
            )
        )

        max_amount = (
            self.request.query_params.get(
                "max_amount"
            )
        )

        if min_amount:
            queryset = queryset.filter(
                amount__gte=min_amount
            )

        if max_amount:
            queryset = queryset.filter(
                amount__lte=max_amount
            )

        return queryset


# =========================================================
# ADMIN DAILY PAYMENT SUMMARY
# =========================================================


class AdminDashboardView(APIView):
    """
    Return daily payment summary for administrators.

    Summary includes:

    - Total transactions
    - Total transaction amount
    - Successful payments
    - Failed payments
    - Pending payments
    """

    permission_classes = [
        IsAdminUserCustom
    ]

    def get(self, request):

        # -------------------------------------------------
        # CURRENT LOCAL DATE
        # -------------------------------------------------

        today = timezone.localdate()

        # -------------------------------------------------
        # LOCAL DAY START / END
        # -------------------------------------------------

        start_of_day, end_of_day = (
            get_local_day_range(today)
        )

        # -------------------------------------------------
        # FILTER TRANSACTIONS FOR TODAY
        # -------------------------------------------------

        transactions = (
            Transaction.objects.filter(
                created_at__gte=start_of_day,
                created_at__lt=end_of_day,
            )
        )

        # -------------------------------------------------
        # AGGREGATE SUMMARY
        # -------------------------------------------------

        summary = transactions.aggregate(

            total_transactions=Count(
                "id"
            ),

            total_amount=Sum(
                "amount"
            ),

            success_count=Count(
                "id",
                filter=Q(
                    status="SUCCESS"
                ),
            ),

            failed_count=Count(
                "id",
                filter=Q(
                    status="FAILED"
                ),
            ),

            pending_count=Count(
                "id",
                filter=Q(
                    status="PENDING"
                ),
            ),
        )

        # -------------------------------------------------
        # ADMIN AUDIT LOG
        # -------------------------------------------------

        AdminLog.objects.create(
            admin=request.user,
            action="VIEW_DAILY_SUMMARY",
            target="DAILY_SUMMARY",
            ip_address=get_client_ip(
                request
            ),
        )

        # -------------------------------------------------
        # RESPONSE
        # -------------------------------------------------

        return Response(
            {
                "date": str(today),

                "total_transactions":
                    summary[
                        "total_transactions"
                    ] or 0,

                "total_amount":
                    summary[
                        "total_amount"
                    ] or 0,

                "success_count":
                    summary[
                        "success_count"
                    ] or 0,

                "failed_count":
                    summary[
                        "failed_count"
                    ] or 0,

                "pending_count":
                    summary[
                        "pending_count"
                    ] or 0,
            }
        )


# =========================================================
# ADMIN CSV EXPORT
# =========================================================


class AdminExportTransactionsView(
    APIView
):
    """
    Export all transactions to CSV.

    Only administrators can access this endpoint.
    """

    permission_classes = [
        IsAdminUserCustom
    ]

    def get(self, request):

        transactions = (
            Transaction.objects
            .select_related(
                "user",
                "card",
            )
            .order_by(
                "-created_at"
            )
        )

        # -------------------------------------------------
        # CSV RESPONSE
        # -------------------------------------------------

        response = HttpResponse(
            content_type="text/csv"
        )

        response[
            "Content-Disposition"
        ] = (
            "attachment; "
            'filename="transactions.csv"'
        )

        writer = csv.writer(
            response
        )

        # -------------------------------------------------
        # CSV HEADER
        # -------------------------------------------------

        writer.writerow(
            [
                "Reference",
                "Username",
                "Email",
                "Card",
                "Amount",
                "Currency",
                "Status",
                "Description",
                "Failure Reason",
                "Created At",
            ]
        )

        # -------------------------------------------------
        # CSV ROWS
        # -------------------------------------------------

        for transaction in transactions:

            writer.writerow(
                [
                    transaction.reference,
                    transaction.user.username,
                    transaction.user.email,
                    transaction.card.masked_number,
                    transaction.amount,
                    transaction.currency,
                    transaction.status,
                    transaction.description,
                    transaction.failure_reason,
                    transaction.created_at,
                ]
            )

        # -------------------------------------------------
        # ADMIN AUDIT LOG
        # -------------------------------------------------

        AdminLog.objects.create(
            admin=request.user,
            action="EXPORT_TRANSACTIONS",
            target="TRANSACTIONS_CSV",
            ip_address=get_client_ip(
                request
            ),
        )

        return response


# =========================================================
# ADMIN CARD MANAGEMENT
# =========================================================


class AdminCardManagementView(APIView):
    """
    Admin-only card management endpoint.

    GET:
        Return all cards with safe activity information.

    PATCH:
        Update card active status and/or credit limit.
    """

    permission_classes = [
        IsAdminUserCustom
    ]

    def get(self, request):

        cards = (
            Card.objects
            .select_related("user")
            .order_by("-created_at")
        )

        response_data = [
            get_card_management_response(card)
            for card in cards
        ]

        AdminLog.objects.create(
            admin=request.user,
            action="VIEW_CARD_MANAGEMENT",
            target="ALL_CARDS",
            ip_address=get_client_ip(
                request
            ),
        )

        return Response(
            response_data,
            status=status.HTTP_200_OK,
        )

    def patch(self, request, pk):

        try:
            card = (
                Card.objects
                .select_related("user")
                .get(pk=pk)
            )

        except Card.DoesNotExist:
            return Response(
                {
                    "detail": "Card not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if not request.data:
            return Response(
                {
                    "detail": (
                        "At least one field is "
                        "required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        allowed_fields = {
            "is_active",
            "credit_limit",
        }

        unsupported_fields = (
            set(request.data.keys())
            - allowed_fields
        )

        if unsupported_fields:
            return Response(
                {
                    "detail": (
                        "Unsupported field(s): "
                        + ", ".join(
                            sorted(
                                unsupported_fields
                            )
                        )
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_is_active = card.is_active
        old_credit_limit = card.credit_limit

        new_is_active = card.is_active
        new_credit_limit = card.credit_limit

        # -------------------------------------------------
        # VALIDATE ACTIVE STATUS
        # -------------------------------------------------

        if "is_active" in request.data:

            value = request.data.get(
                "is_active"
            )

            if not isinstance(value, bool):
                return Response(
                    {
                        "detail": (
                            "is_active must be "
                            "true or false."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            new_is_active = value

        # -------------------------------------------------
        # VALIDATE CREDIT LIMIT
        # -------------------------------------------------

        if "credit_limit" in request.data:

            raw_credit_limit = (
                request.data.get(
                    "credit_limit"
                )
            )

            try:
                new_credit_limit = Decimal(
                    str(raw_credit_limit)
                )

            except (
                InvalidOperation,
                TypeError,
                ValueError,
            ):
                return Response(
                    {
                        "detail": (
                            "credit_limit must "
                            "be a valid number."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if new_credit_limit < 0:
                return Response(
                    {
                        "detail": (
                            "credit_limit cannot "
                            "be negative."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if new_credit_limit > Decimal(
                "9999999999.99"
            ):
                return Response(
                    {
                        "detail": (
                            "credit_limit is "
                            "too large."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if card.card_type == "CREDIT":
                if new_credit_limit <= 0:
                    return Response(
                        {
                            "detail": (
                                "Credit cards must "
                                "have a positive "
                                "credit limit."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            if card.card_type == "DEBIT":
                if new_credit_limit != 0:
                    return Response(
                        {
                            "detail": (
                                "Debit cards must "
                                "have a credit limit "
                                "of 0."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            spent_amount = get_card_spent_amount(
                card
            )

            if new_credit_limit < spent_amount:
                return Response(
                    {
                        "detail": (
                            "Credit limit cannot "
                            "be lower than the "
                            "card's successful "
                            "spending."
                        ),
                        "spent_amount": spent_amount,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # -------------------------------------------------
        # APPLY UPDATE
        # -------------------------------------------------

        with db_transaction.atomic():

            card.is_active = new_is_active
            card.credit_limit = new_credit_limit

            card.save(
                update_fields=[
                    "is_active",
                    "credit_limit",
                ]
            )

            AdminLog.objects.create(
                admin=request.user,
                action="UPDATE_CARD",
                target=f"CARD_{card.id}",
                ip_address=get_client_ip(
                    request
                ),
            )

            # -------------------------------------------------
            # CARD BLOCK EMAIL
            # -------------------------------------------------

            if (
                old_is_active
                and not new_is_active
            ):
                db_transaction.on_commit(
                    lambda card_id=card.id: (
                        self._send_card_blocked_alert(
                            card_id
                        )
                    )
                )

            # -------------------------------------------------
            # LOW CREDIT EMAIL
            # -------------------------------------------------

            if (
                new_is_active
                and card.card_type == "CREDIT"
            ):
                spent_amount = (
                    get_card_spent_amount(
                        card
                    )
                )

                available_credit = (
                    new_credit_limit
                    - spent_amount
                )

                if available_credit < 0:
                    available_credit = Decimal(
                        "0.00"
                    )

                old_available_credit = (
                    old_credit_limit
                    - spent_amount
                )

                if old_available_credit < 0:
                    old_available_credit = (
                        Decimal("0.00")
                    )

                old_percent = (
                    (
                        old_available_credit
                        / old_credit_limit
                    )
                    if old_credit_limit > 0
                    else Decimal("0")
                )

                new_percent = (
                    (
                        available_credit
                        / new_credit_limit
                    )
                    if new_credit_limit > 0
                    else Decimal("0")
                )

                if (
                    old_percent >= Decimal("0.10")
                    and new_percent < Decimal("0.10")
                ):
                    db_transaction.on_commit(
                        lambda card_id=card.id: (
                            self._send_low_credit_alert(
                                card_id
                            )
                        )
                    )

        card.refresh_from_db()

        return Response(
            get_card_management_response(card),
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def _send_card_blocked_alert(card_id):
        """
        Import notification code only when required.

        Notification failure must never break the
        completed admin card operation.
        """

        try:
            from .notifications import (
                send_card_blocked_alert,
            )

            card = (
                Card.objects
                .select_related("user")
                .get(pk=card_id)
            )

            send_card_blocked_alert(
                card
            )

        except Exception:
            return

    @staticmethod
    def _send_low_credit_alert(card_id):
        """
        Send a low-credit notification after the
        database transaction has been committed.
        """

        try:
            from .notifications import (
                send_low_credit_alert,
            )

            card = (
                Card.objects
                .select_related("user")
                .get(pk=card_id)
            )

            spent_amount = get_card_spent_amount(
                card
            )

            available_credit = (
                card.credit_limit
                - spent_amount
            )

            if available_credit < 0:
                available_credit = Decimal(
                    "0.00"
                )

            send_low_credit_alert(
                card,
                available_credit,
            )

        except Exception:
            return


# =========================================================
# MONTHLY STATEMENT PDF
# =========================================================


class MonthlyStatementView(APIView):
    """
    Generate a monthly credit-card statement PDF
    for the currently authenticated user.

    Query parameters:

        year=2026
        month=10
    """

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):

        # -------------------------------------------------
        # READ QUERY PARAMETERS
        # -------------------------------------------------

        year_value = (
            request.query_params.get(
                "year"
            )
        )

        month_value = (
            request.query_params.get(
                "month"
            )
        )

        current_year = (
            timezone.localdate().year
        )

        # -------------------------------------------------
        # VALIDATE YEAR
        # -------------------------------------------------

        try:
            year = int(year_value)

        except (
            TypeError,
            ValueError,
        ):
            return Response(
                {
                    "detail": (
                        "year must be a valid "
                        "number."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            year < 2000
            or year > current_year + 1
        ):
            return Response(
                {
                    "detail": (
                        "year is outside the "
                        "supported range."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -------------------------------------------------
        # VALIDATE MONTH
        # -------------------------------------------------

        try:
            month = int(month_value)

        except (
            TypeError,
            ValueError,
        ):
            return Response(
                {
                    "detail": (
                        "month must be a valid "
                        "number."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if month < 1 or month > 12:
            return Response(
                {
                    "detail": (
                        "month must be between "
                        "1 and 12."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -------------------------------------------------
        # MONTH START / END
        # -------------------------------------------------

        current_timezone = (
            timezone.get_current_timezone()
        )

        month_start_date = datetime(
            year,
            month,
            1,
        ).date()

        if month == 12:
            next_month_date = datetime(
                year + 1,
                1,
                1,
            ).date()
        else:
            next_month_date = datetime(
                year,
                month + 1,
                1,
            ).date()

        month_start = timezone.make_aware(
            datetime.combine(
                month_start_date,
                time.min,
            ),
            current_timezone,
        )

        month_end = timezone.make_aware(
            datetime.combine(
                next_month_date,
                time.min,
            ),
            current_timezone,
        )

        # -------------------------------------------------
        # FETCH USER TRANSACTIONS
        # -------------------------------------------------

        transactions = (
            Transaction.objects
            .filter(
                user=request.user,
                created_at__gte=month_start,
                created_at__lt=month_end,
            )
            .select_related("card")
            .order_by("created_at")
        )

        transaction_list = list(
            transactions
        )

        # -------------------------------------------------
        # CALCULATE SUMMARY
        # -------------------------------------------------

        total_transactions = len(
            transaction_list
        )

        total_spending = sum(
            (
                transaction.amount
                for transaction in transaction_list
                if transaction.status == "SUCCESS"
            ),
            Decimal("0.00"),
        )

        success_count = sum(
            1
            for transaction in transaction_list
            if transaction.status == "SUCCESS"
        )

        failed_count = sum(
            1
            for transaction in transaction_list
            if transaction.status == "FAILED"
        )

        pending_count = sum(
            1
            for transaction in transaction_list
            if transaction.status == "PENDING"
        )

        # -------------------------------------------------
        # IMPORT REPORTLAB ONLY WHEN PDF IS REQUESTED
        # -------------------------------------------------

        try:
            from io import BytesIO

            from reportlab.lib import colors
            from reportlab.lib.enums import TA_LEFT
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import (
                ParagraphStyle,
                getSampleStyleSheet,
            )
            from reportlab.lib.units import mm
            from reportlab.platypus import (
                Paragraph,
                SimpleDocTemplate,
                Spacer,
                Table,
                TableStyle,
            )

        except ImportError:
            return Response(
                {
                    "detail": (
                        "PDF generation dependency "
                        "is not installed yet."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # -------------------------------------------------
        # CREATE PDF BUFFER
        # -------------------------------------------------

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
            "StatementTitle",
            parent=styles["Title"],
            fontSize=20,
            leading=24,
            alignment=TA_LEFT,
            spaceAfter=4,
        )

        subtitle_style = ParagraphStyle(
            "StatementSubtitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            alignment=TA_LEFT,
        )

        section_style = ParagraphStyle(
            "Section",
            parent=styles["Heading2"],
            fontSize=12,
            leading=15,
            spaceBefore=8,
            spaceAfter=6,
        )

        normal_style = ParagraphStyle(
            "NormalText",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
        )

        right_style = ParagraphStyle(
            "RightText",
            parent=normal_style,
            alignment=2,
        )

        story = []

        # -------------------------------------------------
        # HEADER
        # -------------------------------------------------

        story.append(
            Paragraph(
                "CreditPay",
                title_style,
            )
        )

        story.append(
            Paragraph(
                "Monthly Credit Card Statement",
                subtitle_style,
            )
        )

        story.append(
            Spacer(
                1,
                6 * mm,
            )
        )

        # -------------------------------------------------
        # CUSTOMER INFORMATION
        # -------------------------------------------------

        customer_name = (
            request.user.get_full_name()
            or request.user.username
        )

        customer_email = (
            getattr(
                request.user,
                "email",
                "",
            )
            or "Not available"
        )

        statement_month = datetime(
            year,
            month,
            1,
        ).strftime("%B %Y")

        customer_table = Table(
            [
                [
                    Paragraph(
                        "<b>Customer</b>",
                        normal_style,
                    ),
                    Paragraph(
                        str(customer_name),
                        normal_style,
                    ),
                    Paragraph(
                        "<b>Statement Period</b>",
                        normal_style,
                    ),
                    Paragraph(
                        statement_month,
                        normal_style,
                    ),
                ],
                [
                    Paragraph(
                        "<b>Email</b>",
                        normal_style,
                    ),
                    Paragraph(
                        str(customer_email),
                        normal_style,
                    ),
                    Paragraph(
                        "<b>Total Transactions</b>",
                        normal_style,
                    ),
                    Paragraph(
                        str(total_transactions),
                        right_style,
                    ),
                ],
            ],
            colWidths=[
                28 * mm,
                63 * mm,
                38 * mm,
                43 * mm,
            ],
        )

        customer_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, -1),
                        colors.HexColor(
                            "#F5F7FA"
                        ),
                    ),
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.HexColor(
                            "#D0D7DE"
                        ),
                    ),
                    (
                        "INNERGRID",
                        (0, 0),
                        (-1, -1),
                        0.25,
                        colors.HexColor(
                            "#E5E7EB"
                        ),
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                ]
            )
        )

        story.append(
            customer_table
        )

        story.append(
            Spacer(
                1,
                5 * mm,
            )
        )

        # -------------------------------------------------
        # SUMMARY INFORMATION
        # -------------------------------------------------

        story.append(
            Paragraph(
                "Statement Summary",
                section_style,
            )
        )

        summary_table = Table(
            [
                [
                    Paragraph(
                        "<b>Total Spending</b>",
                        normal_style,
                    ),
                    Paragraph(
                        f"INR {total_spending:,.2f}",
                        right_style,
                    ),
                ],
                [
                    Paragraph(
                        "<b>Successful</b>",
                        normal_style,
                    ),
                    Paragraph(
                        str(success_count),
                        right_style,
                    ),
                ],
                [
                    Paragraph(
                        "<b>Failed</b>",
                        normal_style,
                    ),
                    Paragraph(
                        str(failed_count),
                        right_style,
                    ),
                ],
                [
                    Paragraph(
                        "<b>Pending</b>",
                        normal_style,
                    ),
                    Paragraph(
                        str(pending_count),
                        right_style,
                    ),
                ],
            ],
            colWidths=[
                65 * mm,
                75 * mm,
            ],
        )

        summary_table.setStyle(
            TableStyle(
                [
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.HexColor(
                            "#D0D7DE"
                        ),
                    ),
                    (
                        "INNERGRID",
                        (0, 0),
                        (-1, -1),
                        0.25,
                        colors.HexColor(
                            "#E5E7EB"
                        ),
                    ),
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor(
                            "#EEF4FF"
                        ),
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                ]
            )
        )

        story.append(
            summary_table
        )

        story.append(
            Spacer(
                1,
                5 * mm,
            )
        )

        # -------------------------------------------------
        # TRANSACTION DETAILS
        # -------------------------------------------------

        story.append(
            Paragraph(
                "Transaction Details",
                section_style,
            )
        )

        transaction_data = [
            [
                "Date",
                "Reference",
                "Card",
                "Amount",
                "Status",
            ]
        ]

        for item in transaction_list:

            created_date = (
                timezone.localtime(
                    item.created_at
                ).strftime(
                    "%d-%m-%Y %H:%M"
                )
            )

            amount_text = (
                f"{item.currency} "
                f"{item.amount:,.2f}"
            )

            transaction_data.append(
                [
                    created_date,
                    item.reference,
                    item.card.masked_number,
                    amount_text,
                    item.status,
                ]
            )

        if not transaction_list:

            transaction_data.append(
                [
                    "No transactions",
                    "-",
                    "-",
                    "INR 0.00",
                    "-",
                ]
            )

        transaction_table = Table(
            transaction_data,
            colWidths=[
                28 * mm,
                40 * mm,
                35 * mm,
                32 * mm,
                25 * mm,
            ],
            repeatRows=1,
        )

        transaction_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor(
                            "#1F2937"
                        ),
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold",
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        7.5,
                    ),
                    (
                        "LEADING",
                        (0, 0),
                        (-1, -1),
                        9,
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.3,
                        colors.HexColor(
                            "#D1D5DB"
                        ),
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        story.append(
            transaction_table
        )

        story.append(
            Spacer(
                1,
                6 * mm,
            )
        )

        # -------------------------------------------------
        # SECURITY NOTE
        # -------------------------------------------------

        security_note = (
            "<b>Security Notice:</b> "
            "This statement displays only masked card "
            "information. Full card numbers, CVV, and "
            "other sensitive authentication information "
            "are not included."
        )

        story.append(
            Paragraph(
                security_note,
                normal_style,
            )
        )

        # -------------------------------------------------
        # BUILD PDF
        # -------------------------------------------------

        document.build(
            story
        )

        pdf_data = buffer.getvalue()

        buffer.close()

        # -------------------------------------------------
        # PDF RESPONSE
        # -------------------------------------------------

        response = HttpResponse(
            pdf_data,
            content_type="application/pdf",
        )

        response[
            "Content-Disposition"
        ] = (
            "attachment; "
            f'filename="creditpay_statement_'
            f'{year}_{month:02d}.pdf"'
        )

        return response