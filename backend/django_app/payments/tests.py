from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APITestCase


User = get_user_model()


class CardManagementTests(
    APITestCase
):

    def setUp(self):

        self.user = User.objects.create_user(
            username="carduser",
            email="card@example.com",
            password="StrongPassword123",
        )

        self.client.force_authenticate(
            user=self.user
        )

    def test_add_card(self):

        payload = {
            "card_type": "CREDIT",
            "card_number": "4111111111111111",
            "cvv": "123",
            "expiry_month": 12,
            "expiry_year": 2030,
        }

        response = self.client.post(
            "/api/cards/",
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["last4"],
            "1111",
        )

        self.assertTrue(
            response.data[
                "masked_number"
            ].endswith("1111")
        )

        self.assertNotIn(
            "card_number",
            response.data,
        )

        self.assertNotIn(
            "cvv",
            response.data,
        )

    def test_invalid_card(self):

        payload = {
            "card_type": "CREDIT",
            "card_number": "1234567890123456",
            "cvv": "123",
            "expiry_month": 12,
            "expiry_year": 2030,
        }

        response = self.client.post(
            "/api/cards/",
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_view_cards(self):

        response = self.client.get(
            "/api/cards/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )