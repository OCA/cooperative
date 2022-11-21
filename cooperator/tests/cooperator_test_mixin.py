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
        # cf load_for_current_company in chart_template.py in account module

        # if these properties are not set, odoo thinks the chart of account was not
        # loaded. The test CAO does not set those properties
        # cf AccountingTestCase

        cls._ensure_account_property_is_set(
            "res.partner", "property_account_receivable_id"
        )
        cls._ensure_account_property_is_set(
            "res.partner", "property_account_payable_id"
        )
        cls._ensure_account_property_is_set(
            "product.template", "property_account_income_id"
        )

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
        subscription_journal_sequence = cls.env.ref(
            "cooperator.sequence_subscription_journal"
        )
        cls.subscription_journal = cls.env["account.journal"].create(
            {
                "name": "Subscriptions Test",
                "code": "SUBJT",
                "type": "sale",
                "sequence_id": subscription_journal_sequence.id,
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
        cls.bank_journal = cls.env["account.journal"].create(
            {"name": "Bank", "type": "bank", "code": "BNK67"}
        )
        cls.payment_method = cls.env.ref("account.account_payment_method_manual_in")

    @classmethod
    def _ensure_account_property_is_set(cls, model, property_name):
        """Ensure the ir.property is set.
        In case it's not: create it with a random account.
        This is useful when testing with partially defined localization
        (especially test chart of account).

        :param model: the name of the model the property is set on
        :param property_name: The name of the property.
        """
        company_id = cls.env.user.company_id
        field_id = cls.env["ir.model.fields"].search(
            [("model", "=", model), ("name", "=", property_name)],
            limit=1,
        )
        property_id = cls.env["ir.property"].search(
            [
                ("company_id", "=", company_id.id),
                ("name", "=", property_name),
                ("res_id", "=", None),
                ("fields_id", "=", field_id.id),
            ],
            limit=1,
        )
        account_id = cls.env["account.account"].search(
            [("company_id", "=", company_id.id)], limit=1
        )
        value_reference = "account.account,%d" % account_id.id
        if property_id and not property_id.value_reference:
            property_id.value_reference = value_reference
        else:
            cls.env["ir.property"].create(
                {
                    "name": property_name,
                    "company_id": company_id.id,
                    "fields_id": field_id.id,
                    "value_reference": value_reference,
                }
            )

    def pay_invoice(self, invoice, payment_date=None):
        ctx = {"active_model": "account.invoice", "active_ids": [invoice.id]}
        register_payments_vals = {
            "journal_id": self.bank_journal.id,
            "payment_method_id": self.payment_method.id,
        }
        if payment_date is not None:
            register_payments_vals["payment_date"] = payment_date
        register_payments = (
            self.env["account.register.payments"]
            .with_context(ctx)
            .create(register_payments_vals)
        )
        register_payments.create_payments()

    def get_dummy_subscription_requests_vals(self):
        return {
            "share_product_id": self.share_y.id,
            "ordered_parts": 2,
            "firstname": "first name",
            "lastname": "last name",
            "email": "email@example.net",
            "phone": "dummy phone",
            "address": "dummy street",
            "zip_code": "dummy zip",
            "city": "dummy city",
            "country_id": self.ref("base.be"),
            "lang": "en_US",
            "gender": "other",
            "birthdate": "1980-01-01",
            "iban": "BE60096123456870",
            "source": "manual",
        }

    def get_dummy_company_subscription_requests_vals(self):
        vals = self.get_dummy_subscription_requests_vals()
        vals["is_company"] = True
        vals["company_name"] = "dummy company"
        vals["company_email"] = "companyemail@example.net"
        vals["company_register_number"] = "dummy company register number"
        vals["contact_person_function"] = "dummy contact person function"
        return vals

    def create_dummy_subscription_from_partner(self, partner):
        vals = self.get_dummy_subscription_requests_vals()
        vals["partner_id"] = partner.id
        return self.env["subscription.request"].create(vals)

    def create_dummy_subscription_from_company_partner(self, partner):
        vals = self.get_dummy_company_subscription_requests_vals()
        vals["partner_id"] = partner.id
        return self.env["subscription.request"].create(vals)

    def validate_subscription_request_and_pay(self, subscription_request):
        subscription_request.validate_subscription_request()
        self.pay_invoice(subscription_request.capital_release_request)

    def create_dummy_cooperator(self):
        partner = self.env["res.partner"].create(
            {
                "name": "dummy partner 1",
            }
        )
        subscription_request = self.create_dummy_subscription_from_partner(partner)
        self.validate_subscription_request_and_pay(subscription_request)
        return partner

    def create_dummy_company_cooperator(self):
        partner = self.env["res.partner"].create(
            {
                "name": "dummy company partner 1",
                "is_company": True,
            }
        )
        subscription_request = self.create_dummy_subscription_from_company_partner(
            partner
        )
        self.validate_subscription_request_and_pay(subscription_request)
        return partner
