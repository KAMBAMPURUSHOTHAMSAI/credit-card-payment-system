from django.contrib.auth import get_user_model
from rest_framework import serializers


User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={
            "input_type": "password"
        },
    )

    password_confirm = serializers.CharField(
        write_only=True,
        style={
            "input_type": "password"
        },
    )

    class Meta:
        model = User

        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
            "password_confirm",
        ]

    def validate_email(self, value):
        value = value.lower().strip()

        if User.objects.filter(
            email__iexact=value
        ).exists():
            raise serializers.ValidationError(
                "Email is already registered."
            )

        return value

    def validate(self, attrs):
        if (
            attrs["password"]
            != attrs["password_confirm"]
        ):
            raise serializers.ValidationError(
                {
                    "password_confirm":
                    "Passwords do not match."
                }
            )

        return attrs

    def create(self, validated_data):
        validated_data.pop(
            "password_confirm"
        )

        password = validated_data.pop(
            "password"
        )

        user = User(
            **validated_data
        )

        # Django hashes password.
        user.set_password(password)

        user.save()

        return user