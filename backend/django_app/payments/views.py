import csv
from datetime import datetime, time, timedelta

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