from django.urls import path

from .views import (
    AdminCardManagementView,
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

    path(
        "cards/",
        AdminCardManagementView.as_view(),
        name="admin-card-management",
    ),

    path(
        "cards/<int:pk>/",
        AdminCardManagementView.as_view(),
        name="admin-card-update",
    ),
]