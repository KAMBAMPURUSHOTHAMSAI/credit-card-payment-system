from django.contrib import admin
from django.urls import (
    include,
    path,
)

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)


urlpatterns = [

    # Django admin
    path(
        "admin/",
        admin.site.urls,
    ),

    # Authentication
    path(
        "api/auth/",
        include(
            "accounts.urls"
        ),
    ),

    # Cards
    path(
        "api/cards/",
        include(
            "payments.card_urls"
        ),
    ),

    # Transactions
    path(
        "api/transactions/",
        include(
            "payments.transaction_urls"
        ),
    ),

    # Admin APIs
    path(
        "api/admin/",
        include(
            "payments.admin_urls"
        ),
    ),

    # OpenAPI schema
    path(
        "api/schema/",
        SpectacularAPIView.as_view(),
        name="schema",
    ),

    # Swagger UI
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(
            url_name="schema"
        ),
        name="swagger-ui",
    ),
]