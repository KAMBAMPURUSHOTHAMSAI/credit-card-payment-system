from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase


User = get_user_model()


class AuthenticationTests(
    APITestCase
):

    def test_user_registration(self):

        payload = {
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "StrongPassword123",
            "password_confirm": "StrongPassword123",
        }

        response = self.client.post(
            "/api/auth/register/",
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertTrue(
            User.objects.filter(
                username="testuser"
            ).exists()
        )

    def test_user_login(self):

        User.objects.create_user(
            username="loginuser",
            email="login@example.com",
            password="StrongPassword123",
        )

        response = self.client.post(
            "/api/auth/login/",
            {
                "username": "loginuser",
                "password": "StrongPassword123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            "access",
            response.data,
        )

        self.assertIn(
            "refresh",
            response.data,
        )

    def test_invalid_login(self):

        User.objects.create_user(
            username="wronguser",
            email="wrong@example.com",
            password="CorrectPassword123",
        )

        response = self.client.post(
            "/api/auth/login/",
            {
                "username": "wronguser",
                "password": "WrongPassword123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_password_is_hashed(self):

        user = User.objects.create_user(
            username="hashuser",
            email="hash@example.com",
            password="StrongPassword123",
        )

        self.assertNotEqual(
            user.password,
            "StrongPassword123",
        )

        self.assertTrue(
            user.check_password(
                "StrongPassword123"
            )
        )