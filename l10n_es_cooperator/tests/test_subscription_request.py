from datetime import date, datetime, timedelta

from odoo.tests.common import SavepointCase


class TestSubscriptionRequest(SavepointCase):
    def setUp(self):
        super().setUp()
        self.env = self.env(context=dict(self.env.context, tracking_disable=True))
        # accounting data needs to be created even if created in module data
        # because when launching tests, accounting data will be deleted when odoo loads
        # a test chart of account.
        # cf _load in chart_template.py in account module

        account_model = self.env["account.account"]
        self.company = self.env.user.company_id
        self.company.coop_email_contact = "coop_email@example.org"
        self.demo_partner = self.env.ref("base.partner_demo")

        receivable_account_type = self.env.ref("account.data_account_type_receivable")
        equity_account_type = self.env.ref("account.data_account_type_equity")
        cooperator_account = account_model.create(
            {
                "name": "Cooperator Test",
                "code": "416109",
                "user_type_id": receivable_account_type.id,
                "reconcile": True,
            }
        )
        self.company.property_cooperator_account = cooperator_account
        self.equity_account = account_model.create(
            {
                "name": "Equity Test ",
                "code": "100919",
                "user_type_id": equity_account_type.id,
                "reconcile": True,
            }
        )
        self.subscription_journal = self.env["account.journal"].create(
            {
                "name": "Subscriptions Test",
                "code": "SUBJT",
                "type": "sale",
            }
        )

        self.share_x = self.env["product.product"].create(
            {
                "name": "Share X - Founder",
                "short_name": "Part X",
                "is_share": True,
                "by_individual": True,
                "by_company": False,
                "list_price": 50,
            }
        )
        self.share_y = self.env["product.product"].create(
            {
                "name": "Share Y - Worker",
                "short_name": "Part Y",
                "is_share": True,
                "default_share_product": True,
                "by_individual": True,
                "by_company": True,
                "list_price": 25,
            }
        )
        self.subscription_request_1 = self.env["subscription.request"].create(
            {
                "firstname": "John",
                "lastname": "Doe",
                "email": "john@test.com",
                "address": "Cooperation Street",
                "zip_code": "1111",
                "city": "Brussels",
                "lang": "en_US",
                "country_id": self.env.ref("base.be").id,
                "date": datetime.now() - timedelta(days=12),
                "source": "manual",
                "ordered_parts": 3,
                "share_product_id": self.share_y.id,
                "data_policy_approved": True,
                "internal_rules_approved": True,
                "financial_risk_approved": True,
                "generic_rules_approved": True,
                "gender": "male",
                "iban": "09898765454",
                "birthdate": date(1990, 9, 21),
                "skip_iban_control": True,
            }
        )
        self.bank_journal = self.env["account.journal"].create(
            {"name": "Bank", "type": "bank", "code": "BNK67"}
        )
        self.payment_method = self.env.ref("account.account_payment_method_manual_in")

        self.share_line = self.env["share.line"].create(
            {
                "share_product_id": self.share_x.id,
                "share_number": 2,
                "share_unit_price": 50,
                "partner_id": self.demo_partner.id,
                "effective_date": datetime.now() - timedelta(days=120),
            }
        )

    def test_create_subscription_without_partner(self):
        subscription_request = self.env["subscription.request"].create(
            {
                "share_product_id": self.share_y.id,
                "ordered_parts": 2,
                "firstname": "first name",
                "lastname": "last name",
                "email": "email@example.net",
                "phone": "dummy phone",
                "address": "dummy street",
                "zip_code": "dummy zip",
                "city": "dummy city",
                "country_id": self.ref("base.es"),
                "lang": "en_US",
                "gender": "other",
                "birthdate": "1980-01-01",
                "iban": "BE60096123456870",
                "source": "manual",
                "vat": "23917305L",
            }
        )
        self.assertEqual(subscription_request.type, "new")
        self.assertEqual(subscription_request.name, "first name last name")
        self.assertFalse(subscription_request.partner_id)
        subscription_request.validate_subscription_request()
        partner = subscription_request.partner_id
        self.assertTrue(partner)
        self.assertFalse(partner.is_company)
        self.assertEqual(partner.firstname, "first name")
        self.assertEqual(partner.lastname, "last name")
        self.assertEqual(partner.name, "first name last name")
        self.assertEqual(partner.email, "email@example.net")
        self.assertEqual(partner.phone, "dummy phone")
        self.assertEqual(partner.street, "dummy street")
        self.assertEqual(partner.zip, "dummy zip")
        self.assertEqual(partner.city, "dummy city")
        self.assertEqual(partner.country_id, self.browse_ref("base.es"))
        self.assertEqual(partner.lang, "en_US")
        self.assertEqual(partner.gender, "other")
        self.assertEqual(partner.birthdate_date, date(1980, 1, 1))
        self.assertEqual(partner.vat, "23917305L")
        self.assertTrue(partner.cooperator)
