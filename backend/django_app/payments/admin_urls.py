from django.urls import path

from .views import (
    AdminDashboardView,
    AdminExportTransactionsView,
)


urlpatterns = [
    path(
        "dashboard/",
        AdminDashboardView.as_view(),
        name="admin-dashboard",
    ),

    path(
        "transactions/export/",
        AdminExportTransactionsView.as_view(),
        name="admin-export-transactions",
    ),
]