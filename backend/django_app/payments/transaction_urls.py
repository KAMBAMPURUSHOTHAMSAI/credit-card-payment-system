from django.urls import path

from .views import (
    MonthlyStatementView,
    TransactionListView,
)


urlpatterns = [
    path(
        "",
        TransactionListView.as_view(),
        name="transaction-list",
    ),

    path(
        "statement/",
        MonthlyStatementView.as_view(),
        name="monthly-statement",
    ),
]