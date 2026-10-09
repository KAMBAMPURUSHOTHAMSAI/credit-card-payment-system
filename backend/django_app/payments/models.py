
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

    credit_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.card_brand} ****{self.last4}"


class Transaction(models.Model):

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
    ]

    FRAUD_STATUS_CHOICES = [
        ("NOT_CHECKED", "Not Checked"),
        ("CLEAR", "Clear"),
        ("FLAGGED", "Flagged"),
        ("REVIEWED", "Reviewed"),
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

    # Fraud detection result
    fraud_status = models.CharField(
        max_length=15,
        choices=FRAUD_STATUS_CHOICES,
        default="NOT_CHECKED",
        db_index=True,
    )

    # Used for category-wise spending analytics
    category = models.CharField(
        max_length=50,
        default="OTHER",
        blank=True,
        db_index=True,
    )

    # Optional context for fraud detection
    location = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )

    device_id = models.CharField(
        max_length=128,
        blank=True,
        default="",
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
        auto_now_add=True,
        db_index=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["user", "-created_at"],
                name="txn_user_created_idx",
            ),
            models.Index(
                fields=["status", "-created_at"],
                name="txn_status_created_idx",
            ),
        ]

    def __str__(self):
        return f"{self.reference} - {self.status}"


class AdminLog(models.Model):

    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="admin_logs",
    )

    action = models.CharField(
        max_length=100,
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
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.admin.username} - {self.action}"


class FraudLog(models.Model):
    """
    Records suspicious transaction activity and the rule
    that triggered the fraud alert.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fraud_logs",
    )

    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fraud_logs",
    )

    rule_code = models.CharField(
        max_length=100,
    )

    details = models.TextField(
        blank=True,
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    location = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )

    device_id = models.CharField(
        max_length=128,
        blank=True,
        default="",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["rule_code", "-created_at"],
                name="fraud_rule_created_idx",
            ),
        ]

    def __str__(self):
        return f"{self.rule_code} - {self.created_at}"
