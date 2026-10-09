from django.urls import path

from .views import (
    AdminAnalyticsExportView,
    AdminAnalyticsView,
    AdminCardManagementView,
    AdminDashboardView,
    AdminExportTransactionsView,
    AdminHealthView,
)


urlpatterns = [
    # Admin dashboard
    path(
        "dashboard/",
        AdminDashboardView.as_view(),
        name="admin-dashboard",
    ),

    # Transaction CSV export
    path(
        "transactions/export/",
        AdminExportTransactionsView.as_view(),
        name="admin-export-transactions",
    ),

    # Card management
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

    # Analytics dashboard
    path(
        "analytics/",
        AdminAnalyticsView.as_view(),
        name="admin-analytics",
    ),

    # Analytics CSV/PDF export
    path(
        "analytics/export/",
        AdminAnalyticsExportView.as_view(),
        name="admin-analytics-export",
    ),

    # System health monitoring
    path(
        "health/",
        AdminHealthView.as_view(),
        name="admin-health",
    ),
]