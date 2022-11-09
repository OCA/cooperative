# Copyright 2019 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date, datetime, timedelta


class CooperatorTestMixin:
    @classmethod
    def set_up_cooperator_test_data(cls):
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        # accounting data needs to be created even if created in module data
        # because when launching tests, accounting data will be deleted when odoo loads
        # a test chart of account.
        # cf _load in chart_template.py in account module

        account_model = cls.env["account.account"]
        cls.company = cls.env.user.company_id
        cls.company.coop_email_contact = "coop_email@example.org"
        cls.demo_partner = cls.env.ref("base.partner_demo")

        receivable_account_type = cls.env.ref("account.data_account_type_receivable")
        equity_account_type = cls.env.ref("account.data_account_type_equity")
        cooperator_account = account_model.create(
            {
                "name": "Cooperator Test",
                "code": "416109",
                "user_type_id": receivable_account_type.id,
                "reconcile": True,
            }
        )
        cls.company.property_cooperator_account = cooperator_account
        cls.equity_account = account_model.create(
            {
                "name": "Equity Test ",
                "code": "100919",
                "user_type_id": equity_account_type.id,
                "reconcile": True,
            }
        )
        cls.subscription_journal = cls.env["account.journal"].create(
            {
                "name": "Subscriptions Test",
                "code": "SUBJT",
                "type": "sale",
            }
        )

        cls.share_x = cls.env["product.product"].create(
            {
                "name": "Share X - Founder",
                "short_name": "Part X",
                "is_share": True,
                "by_individual": True,
                "by_company": False,
                "list_price": 50,
            }
        )
        cls.share_y = cls.env["product.product"].create(
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
        cls.subscription_request_1 = cls.env["subscription.request"].create(
            {
                "firstname": "John",
                "lastname": "Doe",
                "email": "john@test.com",
                "address": "Cooperation Street",
                "zip_code": "1111",
                "city": "Brussels",
                "lang": "en_US",
                "country_id": cls.env.ref("base.be").id,
                "date": datetime.now() - timedelta(days=12),
                "source": "manual",
                "ordered_parts": 3,
                "share_product_id": cls.share_y.id,
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
