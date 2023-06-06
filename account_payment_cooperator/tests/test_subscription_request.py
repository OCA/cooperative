from datetime import date, datetime, timedelta

from odoo.tests.common import TransactionCase


class TestSubscriptionRequest(TransactionCase):
    def setUp(self):
        super().setUp()
        account_model = self.env["account.account"]
        self.company = self.env.user.company_id

        receivable_account_type = self.env.ref("account.data_account_type_receivable")
        cooperator_account = account_model.create(
            {
                "name": "Cooperator Test",
                "code": "416109",
                "user_type_id": receivable_account_type.id,
                "reconcile": True,
            }
        )
        self.company.property_cooperator_account = cooperator_account

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

        self.bank_journal = self.env["account.journal"].create(
            {"name": "Bank", "type": "bank", "code": "BNK67"}
        )
        self.payment_method = self.env.ref("account.account_payment_method_manual_in")

        self.payment_mode_fixed = self.env["account.payment.mode"].create(
            {
                "name": "Payment Mode Test ",
                "bank_account_link": "fixed",
                "payment_method_id": self.env.ref(
                    "account.account_payment_method_manual_in"
                ).id,
                "fixed_journal_id": self.bank_journal.id,
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
                "payment_mode_id": self.payment_mode_fixed.id,
            }
        )

    def test_validate_subscription_request_invoice_payment_mode_id(self):
        account_move = self.subscription_request_1.validate_subscription_request()
        self.assertEqual(
            self.subscription_request_1.payment_mode_id, account_move.payment_mode_id
        )
        self.assertEqual(
            self.subscription_request_1.payment_mode_id.fixed_journal_id.bank_account_id,
            account_move.partner_bank_id,
        )
