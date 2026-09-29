from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegisterSerializer


class RegisterView(generics.CreateAPIView):
    """
    Register a new user.
    """

    serializer_class = RegisterSerializer
    permission_classes = [
        AllowAny
    ]


class LoginView(TokenObtainPairView):
    """
    JWT login endpoint.
    """

    serializer_class = TokenObtainPairSerializer


class RefreshTokenView(TokenRefreshView):
    """
    Generate a new access token.
    """

    pass


class LogoutView(generics.GenericAPIView):
    """
    Blacklist refresh token during logout.
    """

    def post(self, request):
        refresh_token = request.data.get(
            "refresh"
        )

        if not refresh_token:
            return Response(
                {
                    "detail":
                    "Refresh token is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(
                refresh_token
            )

            token.blacklist()

            return Response(
                {
                    "detail":
                    "Successfully logged out."
                },
                status=status.HTTP_205_RESET_CONTENT,
            )

        except Exception:
            return Response(
                {
                    "detail":
                    "Invalid or expired refresh token."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )