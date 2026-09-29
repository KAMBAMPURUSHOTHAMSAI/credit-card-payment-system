from django.urls import path

from .views import (
    CardListCreateView,
    CardDeleteView,
)


urlpatterns = [
    path(
        "",
        CardListCreateView.as_view(),
        name="card-list-create",
    ),

    path(
        "<int:pk>/",
        CardDeleteView.as_view(),
        name="card-delete",
    ),
]