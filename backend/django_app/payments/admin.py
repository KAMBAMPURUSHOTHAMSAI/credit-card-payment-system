from django.contrib import admin

from .models import (
    Card,
    Transaction,
    AdminLog,
)


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):

    list_display = [
        "id",
        "user",
        "card_brand",
        "masked_number",
        "card_type",
        "expiry_month",
        "expiry_year",
        "is_active",
        "created_at",
    ]

    search_fields = [
        "user__username",
        "user__email",
        "last4",
    ]

    list_filter = [
        "card_type",
        "card_brand",
        "is_active",
    ]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):

    list_display = [
        "reference",
        "user",
        "card",
        "amount",
        "currency",
        "status",
        "created_at",
    ]

    search_fields = [
        "reference",
        "user__username",
        "user__email",
    ]

    list_filter = [
        "status",
        "currency",
    ]

    readonly_fields = [
        "reference",
        "created_at",
        "updated_at",
    ]


@admin.register(AdminLog)
class AdminLogAdmin(admin.ModelAdmin):

    list_display = [
        "admin",
        "action",
        "target",
        "ip_address",
        "created_at",
    ]

    list_filter = [
        "action",
    ]

    search_fields = [
        "admin__username",
        "action",
        "target",
    ]

    readonly_fields = [
        "created_at",
    ]