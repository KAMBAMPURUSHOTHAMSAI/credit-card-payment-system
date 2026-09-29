from django.conf import settings
from django.db import models


class Card(models.Model):

    CARD_TYPES = [
        ("CREDIT", "Credit"),
        ("DEBIT", "Debit"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cards",
    )

    card_type = models.CharField(
        max_length=10,
        choices=CARD_TYPES,
    )

    card_brand = models.CharField(
        max_length=30,
    )

    masked_number = models.CharField(
        max_length=20,
    )

    last4 = models.CharField(
        max_length=4,
    )

    expiry_month = models.PositiveSmallIntegerField()

    expiry_year = models.PositiveSmallIntegerField()

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = [
            "-created_at"
        ]

    def __str__(self):
        return (
            f"{self.card_brand} "
            f"****{self.last4}"
        )


class Transaction(models.Model):

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="transactions",
    )

    card = models.ForeignKey(
        Card,
        on_delete=models.PROTECT,
        related_name="transactions",
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    currency = models.CharField(
        max_length=3,
        default="INR",
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="PENDING",
    )

    reference = models.CharField(
        max_length=64,
        unique=True,
    )

    description = models.CharField(
        max_length=255,
        blank=True,
    )

    failure_reason = models.CharField(
        max_length=255,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = [
            "-created_at"
        ]

    def __str__(self):
        return (
            f"{self.reference} - "
            f"{self.status}"
        )


class AdminLog(models.Model):

    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="admin_logs",
    )

    action = models.CharField(
        max_length=100
    )

    target = models.CharField(
        max_length=100,
        blank=True,
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = [
            "-created_at"
        ]

    def __str__(self):
        return (
            f"{self.admin.username} - "
            f"{self.action}"
        )