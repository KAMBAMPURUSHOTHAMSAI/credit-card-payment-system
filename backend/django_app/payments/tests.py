
from decimal import Decimal
from importlib.util import find_spec

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from .models import AdminLog, Card, FraudLog, Transaction


User = get_user_model()


def assign_role(user, role_name):
    """Assign an application role using Django's built-in Groups."""
    group, _ = Group.objects.get_or_create(name=role_name)
    user.groups.add(group)
    return group


# =========================================================
# EXISTING CARD MANAGEMENT TESTS
# =========================================================

class CardManagementTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="carduser",
            email="card@example.com",
            password="StrongPassword123",
        )
        self.client.force_authenticate(user=self.user)

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

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["last4"], "1111")
        self.assertTrue(response.data["masked_number"].endswith("1111"))
        self.assertNotIn("card_number", response.data)
        self.assertNotIn("cvv", response.data)

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

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_view_cards(self):
        response = self.client.get("/api/cards/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# =========================================================
# TRANSACTION SEARCH, FILTERS AND PAGINATION
# =========================================================

class TransactionSearchTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="searchuser",
            email="search@example.com",
            password="StrongPassword123",
        )
        self.other_user = User.objects.create_user(
            username="othersearchuser",
            email="other-search@example.com",
            password="StrongPassword123",
        )

        self.card = Card.objects.create(
            user=self.user,
            card_type="CREDIT",
            card_brand="VISA",
            masked_number="************5555",
            last4="5555",
            expiry_month=12,
            expiry_year=2030,
            credit_limit=Decimal("10000.00"),
            is_active=True,
        )
        self.other_card = Card.objects.create(
            user=self.other_user,
            card_type="CREDIT",
            card_brand="VISA",
            masked_number="************9999",
            last4="9999",
            expiry_month=12,
            expiry_year=2030,
            credit_limit=Decimal("5000.00"),
            is_active=True,
        )

        for index in range(12):
            Transaction.objects.create(
                user=self.user,
                card=self.card,
                amount=Decimal("100.00") + Decimal(index * 100),
                currency="INR",
                status="SUCCESS" if index % 2 == 0 else "FAILED",
                fraud_status="FLAGGED" if index == 4 else "CLEAR",
                category="FOOD" if index == 4 else "OTHER",
                reference=f"PAY-SEARCH-{index:03d}",
                description=f"Search transaction {index}",
                failure_reason="",
            )

        Transaction.objects.create(
            user=self.other_user,
            card=self.other_card,
            amount=Decimal("250.00"),
            currency="INR",
            status="SUCCESS",
            fraud_status="CLEAR",
            category="OTHER",
            reference="PAY-OTHER-001",
            description="Another user's transaction",
            failure_reason="",
        )
        self.client.force_authenticate(user=self.user)

    def test_transaction_list_is_paginated_and_sorted(self):
        response = self.client.get(
            "/api/transactions/?page=1&page_size=5&ordering=amount"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 12)
        self.assertEqual(len(response.data["results"]), 5)
        self.assertEqual(
            Decimal(str(response.data["results"][0]["amount"])),
            Decimal("100.00"),
        )

    def test_transaction_search_filters_status_fraud_amount_and_card(self):
        response = self.client.get(
            "/api/transactions/?status=SUCCESS&fraud_status=FLAGGED"
            "&min_amount=500&max_amount=500&card_search=5555"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

        result = response.data["results"][0]
        self.assertEqual(result["reference"], "PAY-SEARCH-004")
        self.assertEqual(result["fraud_status"], "FLAGGED")
        self.assertEqual(result["category"], "FOOD")

    def test_transaction_search_rejects_invalid_filters(self):
        invalid_status_response = self.client.get(
            "/api/transactions/?status=NOT_A_STATUS"
        )
        self.assertEqual(
            invalid_status_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        invalid_amount_response = self.client.get(
            "/api/transactions/?min_amount=900&max_amount=100"
        )
        self.assertEqual(
            invalid_amount_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        invalid_date_response = self.client.get(
            "/api/transactions/?start_date=not-a-date"
        )
        self.assertEqual(
            invalid_date_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_transaction_list_does_not_expose_other_users_transactions(self):
        response = self.client.get("/api/transactions/?page_size=100")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 12)

        references = {
            item["reference"] for item in response.data["results"]
        }
        self.assertNotIn("PAY-OTHER-001", references)


# =========================================================
# ROLE-BASED ACCESS CONTROL AND AUDIT LOGGING
# =========================================================

class RoleAndAuditLogTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="role-owner",
            email="role-owner@example.com",
            password="StrongPassword123",
        )
        self.admin = User.objects.create_user(
            username="role-admin",
            email="role-admin@example.com",
            password="StrongPassword123",
        )
        self.support = User.objects.create_user(
            username="role-support",
            email="role-support@example.com",
            password="StrongPassword123",
        )
        self.read_only = User.objects.create_user(
            username="role-reader",
            email="role-reader@example.com",
            password="StrongPassword123",
        )

        assign_role(self.admin, "Admin")
        assign_role(self.support, "Support")
        assign_role(self.read_only, "Read-Only")

        self.card = Card.objects.create(
            user=self.owner,
            card_type="CREDIT",
            card_brand="VISA",
            masked_number="************5555",
            last4="5555",
            expiry_month=12,
            expiry_year=2030,
            credit_limit=Decimal("10000.00"),
            is_active=True,
        )
        self.transaction = Transaction.objects.create(
            user=self.owner,
            card=self.card,
            amount=Decimal("250.00"),
            currency="INR",
            status="SUCCESS",
            fraud_status="CLEAR",
            category="FOOD",
            reference="PAY-ROLE-001",
            description="Analytics test transaction",
            failure_reason="",
        )

    def test_user_without_application_role_is_denied_admin_api(self):
        self.client.force_authenticate(user=self.owner)

        analytics_response = self.client.get("/api/admin/analytics/")
        cards_response = self.client.get("/api/admin/cards/")

        self.assertEqual(
            analytics_response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            cards_response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_read_only_role_can_view_but_cannot_change_card(self):
        self.client.force_authenticate(user=self.read_only)

        list_response = self.client.get("/api/admin/cards/")
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)

        update_response = self.client.patch(
            f"/api/admin/cards/{self.card.id}/",
            {"is_active": False},
            format="json",
        )
        self.assertEqual(
            update_response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_support_can_block_card_but_cannot_change_credit_limit(self):
        self.client.force_authenticate(user=self.support)

        block_response = self.client.patch(
            f"/api/admin/cards/{self.card.id}/",
            {"is_active": False},
            format="json",
        )
        self.assertEqual(block_response.status_code, status.HTTP_200_OK)

        self.assertTrue(
            AdminLog.objects.filter(
                admin=self.support,
                action="BLOCK_CARD",
                target=f"CARD_{self.card.id}",
            ).exists()
        )

        limit_response = self.client.patch(
            f"/api/admin/cards/{self.card.id}/",
            {"credit_limit": "12000.00"},
            format="json",
        )
        self.assertEqual(
            limit_response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertFalse(
            AdminLog.objects.filter(
                admin=self.support,
                action="UPDATE_CREDIT_LIMIT",
            ).exists()
        )

    def test_admin_can_update_credit_limit_and_action_is_audited(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.patch(
            f"/api/admin/cards/{self.card.id}/",
            {"credit_limit": "15000.00"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.card.refresh_from_db()
        self.assertEqual(str(self.card.credit_limit), "15000.00")

        self.assertTrue(
            AdminLog.objects.filter(
                admin=self.admin,
                action="UPDATE_CREDIT_LIMIT",
                target__startswith=f"CARD_{self.card.id}",
            ).exists()
        )

    def test_admin_dashboard_permissions_and_audit_log(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.get("/api/admin/dashboard/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("permissions", response.data)
        self.assertTrue(
            response.data["permissions"]["can_manage_card_status"]
        )
        self.assertTrue(
            response.data["permissions"]["can_update_credit_limit"]
        )
        self.assertTrue(
            response.data["permissions"]["can_export_transactions"]
        )

        self.assertTrue(
            AdminLog.objects.filter(
                admin=self.admin,
                action="VIEW_DAILY_SUMMARY",
            ).exists()
        )

    def test_analytics_contains_monthly_category_and_utilization_data(self):
        self.client.force_authenticate(user=self.read_only)

        response = self.client.get("/api/admin/analytics/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["monthly_spending"]), 6)
        self.assertIn("category_spending", response.data)
        self.assertIn("credit_utilization", response.data)

        self.assertTrue(
            any(
                item["category"] == "FOOD"
                for item in response.data["category_spending"]
            )
        )
        self.assertTrue(
            AdminLog.objects.filter(
                admin=self.read_only,
                action="VIEW_ANALYTICS_SUMMARY",
            ).exists()
        )

    def test_analytics_csv_export_and_invalid_format(self):
        self.client.force_authenticate(user=self.support)

        csv_response = self.client.get(
            "/api/admin/analytics/export/?format=csv"
        )
        self.assertEqual(csv_response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            csv_response["Content-Type"].startswith("text/csv")
        )
        self.assertIn(b"Monthly Spending", csv_response.content)

        self.assertTrue(
            AdminLog.objects.filter(
                admin=self.support,
                action="EXPORT_ANALYTICS_CSV",
            ).exists()
        )

        invalid_response = self.client.get(
            "/api/admin/analytics/export/?format=xml"
        )
        self.assertEqual(
            invalid_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_analytics_pdf_export(self):
        if find_spec("reportlab") is None:
            self.skipTest("ReportLab is not installed in this environment.")

        self.client.force_authenticate(user=self.support)
        response = self.client.get("/api/admin/analytics/export/?format=pdf")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))

        self.assertTrue(
            AdminLog.objects.filter(
                admin=self.support,
                action="EXPORT_ANALYTICS_PDF",
            ).exists()
        )

    def test_transaction_csv_export_is_role_protected_and_audited(self):
        self.client.force_authenticate(user=self.support)

        response = self.client.get("/api/admin/transactions/export/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response["Content-Type"].startswith("text/csv"))
        self.assertIn(b"PAY-ROLE-001", response.content)

        self.assertTrue(
            AdminLog.objects.filter(
                admin=self.support,
                action="EXPORT_TRANSACTIONS",
            ).exists()
        )

    def test_health_endpoint_reports_database_and_writes_audit_log(self):
        self.client.force_authenticate(user=self.read_only)

        response = self.client.get("/api/admin/health/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(response.data["status"], {"healthy", "degraded"})
        self.assertIn(
            response.data["database_status"],
            {"connected", "unavailable"},
        )
        self.assertIn("response_time_ms", response.data)

        self.assertTrue(
            AdminLog.objects.filter(
                admin=self.read_only,
                action="VIEW_SYSTEM_HEALTH",
            ).exists()
        )

    def test_fraud_log_can_store_signal_metadata(self):
        fraud_log = FraudLog.objects.create(
            user=self.owner,
            transaction=self.transaction,
            rule_code="REPEATED_HIGH_VALUE",
            details="Repeated high-value transaction signal",
            ip_address="127.0.0.1",
            location="Test location",
            device_id="test-device-1",
        )

        self.assertIsNotNone(fraud_log.pk)
        self.assertEqual(fraud_log.rule_code, "REPEATED_HIGH_VALUE")
        self.assertEqual(fraud_log.transaction_id, self.transaction.id)
        self.assertEqual(fraud_log.device_id, "test-device-1")


# =========================================================
# MONTHLY STATEMENT PDF REGRESSION TEST
# =========================================================

class MonthlyStatementRegressionTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="statementuser",
            email="statement@example.com",
            password="StrongPassword123",
        )
        self.card = Card.objects.create(
            user=self.user,
            card_type="CREDIT",
            card_brand="VISA",
            masked_number="************1111",
            last4="1111",
            expiry_month=12,
            expiry_year=2030,
            credit_limit=Decimal("10000.00"),
            is_active=True,
        )
        Transaction.objects.create(
            user=self.user,
            card=self.card,
            amount=Decimal("1000.00"),
            currency="INR",
            status="SUCCESS",
            fraud_status="CLEAR",
            category="OTHER",
            reference="PAY-STATEMENT-REGRESSION-001",
            description="Statement regression test",
            failure_reason="",
        )

    def test_monthly_statement_returns_pdf_for_authenticated_user(self):
        self.client.force_authenticate(user=self.user)
        today = timezone.localdate()

        response = self.client.get(
            "/api/transactions/statement/",
            {"year": today.year, "month": today.month},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))


# =========================================================
# DJANGO REQUEST MONITORING MIDDLEWARE TEST
# =========================================================

class RequestMonitoringMiddlewareTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="monitoruser",
            email="monitor@example.com",
            password="StrongPassword123",
        )
        self.client.force_authenticate(user=self.user)

    def test_bad_request_is_logged_as_warning(self):
        with self.assertLogs("api.monitoring", level="WARNING") as captured:
            response = self.client.get(
                "/api/transactions/?status=NOT_A_STATUS"
            )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(
            any("status=400" in message for message in captured.output)
        )
