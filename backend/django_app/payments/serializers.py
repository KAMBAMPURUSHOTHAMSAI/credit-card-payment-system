from decimal import Decimal

from rest_framework import serializers

from .models import Card, Transaction

from .services import (
    validate_card_number,
    validate_cvv,
    detect_card_brand,
    create_masked_card_number,
    validate_expiry,
)


class CardSerializer(serializers.ModelSerializer):

    card_number = serializers.CharField(
        write_only=True,
        required=True,
    )

    cvv = serializers.CharField(
        write_only=True,
        required=True,
        min_length=3,
        max_length=4,
    )

    credit_limit = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.00"),
        required=False,
        default=Decimal("0.00"),
    )

    class Meta:
        model = Card

        fields = [
            "id",
            "card_type",
            "card_brand",
            "card_number",
            "cvv",
            "masked_number",
            "last4",
            "expiry_month",
            "expiry_year",
            "credit_limit",
            "is_active",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "card_brand",
            "masked_number",
            "last4",
            "is_active",
            "created_at",
        ]

    def validate(self, attrs):

        card_number = attrs.get("card_number")
        cvv = attrs.get("cvv")
        expiry_month = attrs.get("expiry_month")
        expiry_year = attrs.get("expiry_year")
        card_type = attrs.get("card_type")

        credit_limit = attrs.get(
            "credit_limit",
            Decimal("0.00"),
        )

        try:
            cleaned_number = validate_card_number(
                card_number
            )

            validate_cvv(cvv)

            validate_expiry(
                expiry_month,
                expiry_year,
            )

        except ValueError as exc:
            raise serializers.ValidationError(
                {"detail": str(exc)}
            )

        if card_type == "DEBIT":
            if credit_limit != Decimal("0.00"):
                raise serializers.ValidationError(
                    {
                        "credit_limit": (
                            "Credit limit must be 0 "
                            "for debit cards."
                        )
                    }
                )

        attrs["_cleaned_card_number"] = cleaned_number

        return attrs

    def create(self, validated_data):

        card_number = validated_data.pop(
            "_cleaned_card_number"
        )

        # Never store the actual card number.
        validated_data.pop("card_number", None)

        # Never store the CVV.
        validated_data.pop("cvv", None)

        validated_data["card_brand"] = detect_card_brand(
            card_number
        )

        validated_data["masked_number"] = (
            create_masked_card_number(card_number)
        )

        validated_data["last4"] = card_number[-4:]

        return Card.objects.create(**validated_data)


class TransactionSerializer(serializers.ModelSerializer):

    card_number = serializers.CharField(
        source="card.masked_number",
        read_only=True,
    )

    class Meta:
        model = Transaction

        fields = [
            "id",
            "reference",
            "card",
            "card_number",
            "amount",
            "currency",
            "status",
            "fraud_status",
            "category",
            "description",
            "failure_reason",
            "created_at",
            "updated_at",
        ]

        # Transaction fields remain read-only,
        # including fraud_status and category.
        read_only_fields = fields