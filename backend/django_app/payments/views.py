import csv
import uuid

from django.db.models import (
    Count,
    Sum,
    Q,
)
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from django_filters.rest_framework import (
    DjangoFilterBackend,
)

from rest_framework import (
    generics,
    status,
)
from rest_framework.permissions import (
    IsAuthenticated,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Card,
    Transaction,
    AdminLog,
)

from .serializers import (
    CardSerializer,
    TransactionSerializer,
)

from .permissions import (
    IsAdminUserCustom,
)


def get_client_ip(request):
    forwarded = request.META.get(
        "HTTP_X_FORWARDED_FOR"
    )

    if forwarded:
        return forwarded.split(",")[0]

    return request.META.get(
        "REMOTE_ADDR"
    )


class CardListCreateView(
    generics.ListCreateAPIView
):

    serializer_class = CardSerializer
    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):
        return Card.objects.filter(
            user=self.request.user,
            is_active=True,
        )

    def perform_create(self, serializer):

        serializer.save(
            user=self.request.user
        )


class CardDeleteView(
    generics.DestroyAPIView
):

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
        # Soft delete preserves transaction history.
        instance.is_active = False
        instance.save(
            update_fields=[
                "is_active"
            ]
        )


class TransactionListView(
    generics.ListAPIView
):

    serializer_class = (
        TransactionSerializer
    )

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
        )

        start_date = self.request.query_params.get(
            "start_date"
        )

        end_date = self.request.query_params.get(
            "end_date"
        )

        min_amount = self.request.query_params.get(
            "min_amount"
        )

        max_amount = self.request.query_params.get(
            "max_amount"
        )

        if start_date:
            queryset = queryset.filter(
                created_at__date__gte=start_date
            )

        if end_date:
            queryset = queryset.filter(
                created_at__date__lte=end_date
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


class AdminDashboardView(APIView):

    permission_classes = [
        IsAdminUserCustom
    ]

    def get(self, request):

        today = timezone.localdate()

        transactions = Transaction.objects.filter(
            created_at__date=today
        )

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

        AdminLog.objects.create(
            admin=request.user,
            action="VIEW_DAILY_SUMMARY",
            target="DAILY_SUMMARY",
            ip_address=get_client_ip(
                request
            ),
        )

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


class AdminExportTransactionsView(
    APIView
):

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
                "Created At",
            ]
        )

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
                    transaction.created_at,
                ]
            )

        AdminLog.objects.create(
            admin=request.user,
            action="EXPORT_TRANSACTIONS",
            target="TRANSACTIONS_CSV",
            ip_address=get_client_ip(
                request
            ),
        )

        return response