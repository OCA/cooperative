# SPDX-FileCopyrightText: 2019 Coop IT Easy SC
# SPDX-FileContributor: Robin Keunen <robin@coopiteasy.be>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from datetime import date, datetime, timedelta

from odoo import fields


class CooperatorTestMixin:
    @classmethod
    def set_up_cooperator_test_data(cls):
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("base.main_company")
        cls.company.coop_email_contact = "coop_email@example.org"

        # Asegurar que la cuenta de cooperador está configurada
        if not cls.company.property_cooperator_account:
            account_model = cls.env["account.account"]
            cls.company.property_cooperator_account = account_model.create(
                {
                    "code": "416101",
                    "name": "Cooperators",
                    "account_type": "asset_receivable",
                    "reconcile": True,
                    "company_id": cls.company.id,
                }
            )

        # Configurar cuenta de ingresos para productos de acciones
        income_account = cls._ensure_account(
            cls.company, "income", "700000", "Product Income"
        )

        company_share_category = cls.env.ref(
            "cooperator.product_category_company_share"
        )

        # Asignar cuenta de ingresos a la categoría de producto
        if company_share_category:
            company_share_category.property_account_income_categ_id = income_account

        cls.share_x = cls.env["product.product"].create(
            {
                "name": "Share X - Founder",
                "short_name": "Share X",
                "default_code": "share_x",
                "categ_id": company_share_category.id,
                "is_share": True,
                "by_individual": True,
                "by_company": False,
                "list_price": 50,
                "property_account_income_id": income_account.id,
            }
        )
        cls.share_y = cls.env["product.product"].create(
            {
                "name": "Share Y - Worker",
                "short_name": "Share Y",
                "default_code": "share_y",
                "categ_id": company_share_category.id,
                "is_share": True,
                "default_share_product": True,
                "by_individual": True,
                "by_company": True,
                "list_price": 25,
                "property_account_income_id": income_account.id,
            }
        )
        cls.demo_partner = cls.env.ref("base.partner_demo")
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

    @classmethod
    def _ensure_account(cls, company, account_type, code, name, reconcile=False):
        """Helper to find or create an account."""
        account_model = cls.env["account.account"]
        account = account_model.search(
            [
                ("account_type", "=", account_type),
                ("company_id", "=", company.id),
                ("code", "=", code),
            ],
            limit=1,
        )
        if not account:
            account = account_model.create(
                {
                    "code": code,
                    "name": name,
                    "account_type": account_type,
                    "reconcile": reconcile,
                    "company_id": company.id,
                }
            )
        return account

    @classmethod
    def _ensure_journal(cls, company, journal_type, code, name, default_account):
        """Helper to find or create a journal."""
        journal_model = cls.env["account.journal"]
        journal = journal_model.search(
            [
                ("type", "=", journal_type),
                ("company_id", "=", company.id),
                ("code", "=", code),
            ],
            limit=1,
        )
        if not journal:
            journal = journal_model.create(
                {
                    "name": name,
                    "code": code,
                    "type": journal_type,
                    "company_id": company.id,
                    "default_account_id": default_account.id,
                }
            )
        return journal

    @classmethod
    def _setup_company_payment_methods(cls, company, bank_journal, outstanding_account):
        """Setup payment method lines for Odoo 17 compatibility."""
        payment_method_line_model = cls.env["account.payment.method.line"]
        if not hasattr(payment_method_line_model, "payment_account_id"):
            return  # Skip if field doesn't exist (older versions)

        inbound_method_ref = "account.account_payment_method_manual_in"
        outbound_method_ref = "account.account_payment_method_manual_out"

        inbound_payment_method = cls.env.ref(
            inbound_method_ref, raise_if_not_found=False
        )
        outbound_payment_method = cls.env.ref(
            outbound_method_ref, raise_if_not_found=False
        )

        if inbound_payment_method:
            payment_method_line_model.create(
                {
                    "journal_id": bank_journal.id,
                    "payment_method_id": inbound_payment_method.id,
                    "payment_account_id": outstanding_account.id,
                }
            )

        if outbound_payment_method:
            payment_method_line_model.create(
                {
                    "journal_id": bank_journal.id,
                    "payment_method_id": outbound_payment_method.id,
                    "payment_account_id": outstanding_account.id,
                }
            )

    @classmethod
    def _setup_company_accounting(cls, company):
        """Setup basic accounting configuration for a test company."""
        # Cooperator account
        cooperator_account = cls._ensure_account(
            company, "asset_receivable", "416101", "Cooperators", reconcile=True
        )
        company.property_cooperator_account = cooperator_account

        # Income account
        income_account = cls._ensure_account(
            company, "income", "700000", "Product Income"
        )

        # Bank account
        bank_account = cls._ensure_account(
            company, "asset_cash", "570000", "Bank Account", reconcile=True
        )

        # Outstanding payments account
        outstanding_account = cls._ensure_account(
            company,
            "asset_receivable",
            "551000",
            "Outstanding Payments Account",
            reconcile=True,
        )

        # Configure company-level outstanding accounts
        if hasattr(company, "account_journal_payment_debit_account_id"):
            company.account_journal_payment_debit_account_id = outstanding_account.id
        if hasattr(company, "account_journal_payment_credit_account_id"):
            company.account_journal_payment_credit_account_id = outstanding_account.id

        # Bank Journal
        bank_journal = cls._ensure_journal(
            company, "bank", "TBNK", "Test Bank", bank_account
        )
        cls._setup_company_payment_methods(company, bank_journal, outstanding_account)

        # Subscription Journal
        subscription_income_account = cls._ensure_account(
            company, "income", "701000", "Subscription Income"
        )
        subscription_journal = cls._ensure_journal(
            company, "sale", "SUBJ", "Subscription Journal", subscription_income_account
        )
        company.subscription_journal_id = subscription_journal

        # Assign income account to product category property
        company_share_category = cls.env.ref(
            "cooperator.product_category_company_share"
        )
        if company_share_category:
            field = cls.env["ir.model.fields"].search(
                [
                    ("model", "=", "product.category"),
                    ("name", "=", "property_account_income_categ_id"),
                ],
                limit=1,
            )
            if field:
                property_model = cls.env["ir.property"]
                existing_property = property_model.search(
                    [
                        ("company_id", "=", company.id),
                        (
                            "res_id",
                            "=",
                            f"product.category,{company_share_category.id}",
                        ),
                        ("fields_id", "=", field.id),
                    ],
                    limit=1,
                )
                if not existing_property:
                    property_model.create(
                        {
                            "name": "property_account_income_categ_id",
                            "company_id": company.id,
                            "res_id": f"product.category,{company_share_category.id}",
                            "value_reference": f"account.account,{income_account.id}",
                            "type": "many2one",
                            "fields_id": field.id,
                        }
                    )
            # Alternative method
            if hasattr(company_share_category, "with_company"):
                (
                    company_share_category.with_company(
                        company
                    ).property_account_income_categ_id
                ) = income_account

    @classmethod
    def create_company(cls, name):
        company = cls.env["res.company"].create({"name": name})

        # apply the same account chart template as the main company
        if hasattr(cls.env.company, "account_chart_template_id"):
            cls.env.company.account_chart_template_id.try_loading_for_current_company(
                company
            )

        cls._setup_company_accounting(company)
        return company

    @classmethod
    def pay_invoice(cls, invoice, payment_date=None, force_payment=False):
        if invoice.amount_total <= 0 and not force_payment:
            raise ValueError("The invoice has no outstanding amount to pay.")

        # Ensure correct company context
        ctx = {
            "active_model": "account.move",
            "active_ids": [invoice.id],
            "allowed_company_ids": [invoice.company_id.id],
        }
        register_payments_vals = {"payment_type": "inbound"}
        if payment_date is not None:
            register_payments_vals["payment_date"] = payment_date

        # Use with_company to ensure operating in the correct company
        register_payment = (
            cls.env["account.payment.register"]
            .with_context(**ctx)
            .with_company(invoice.company_id.id)
            .create(register_payments_vals)
        )
        register_payment.action_create_payments()

    @classmethod
    def create_payment_account_move(cls, invoice, date_payment=None, amount=None):
        """Create an account.move that pays the invoice.

        This function is useful when you need to reconcile the invoice
        without going through the whole account.payment workflow.
        """
        if amount is None:
            # Get receivable line
            receivable_line = invoice.line_ids.filtered(
                lambda line: line.account_id.account_type == "asset_receivable"
            )
            if receivable_line:
                amount = abs(receivable_line[0].credit)
            else:
                # Handle case where amount cannot be determined
                raise ValueError("Could not determine invoice amount for payment.")

        # Find or create bank journal for this company
        journal = (
            cls.env["account.journal"]
            .with_company(invoice.company_id)
            .search(
                [("type", "=", "bank"), ("company_id", "=", invoice.company_id.id)],
                limit=1,
            )
        )
        if not journal:
            journal = (
                cls.env["account.journal"]
                .with_company(invoice.company_id)
                .create(
                    {
                        "name": "Bank Test",
                        "code": "BNKT",
                        "type": "bank",
                        "company_id": invoice.company_id.id,
                        # Need a default account for the journal
                        "default_account_id": cls._ensure_account(
                            invoice.company_id,
                            "asset_cash",
                            "570001",
                            "Bank Test Account",
                        ).id,
                    }
                )
            )

        receivable_line = invoice.line_ids.filtered(
            lambda line: line.account_id.account_type == "asset_receivable"
            and not line.reconciled
        )
        if not receivable_line:
            # If no lines to reconcile or already reconciled, do nothing
            return

        # Create payment move
        move = (
            cls.env["account.move"]
            .with_company(invoice.company_id)
            .create(
                {
                    "journal_id": journal.id,
                    "date": date_payment or fields.Date.today(),
                    "ref": "Payment for %s" % invoice.name,
                    "line_ids": [
                        fields.Command.create(
                            {
                                "account_id": receivable_line[0].account_id.id,
                                "debit": amount,
                                "credit": 0,
                                "partner_id": invoice.partner_id.id,
                            }
                        ),
                        fields.Command.create(
                            {
                                "account_id": journal.default_account_id.id,
                                "debit": 0,
                                "credit": amount,
                                "partner_id": invoice.partner_id.id,
                            }
                        ),
                    ],
                }
            )
        )
        move.action_post()

        # Reconcile lines
        move_receivable = move.line_ids.filtered(
            lambda line: line.account_id.account_type == "asset_receivable"
            and not line.reconciled
        )
        invoice_receivable = invoice.line_ids.filtered(
            lambda line: line.account_id.account_type == "asset_receivable"
            and not line.reconciled
        )

        if move_receivable and invoice_receivable:
            (move_receivable + invoice_receivable).reconcile()

        # Ensure effective date updates after reconciliation
        partner = invoice.partner_id
        partner.invalidate_recordset()
        if hasattr(partner, "cooperative_membership_id"):
            partner.cooperative_membership_id.invalidate_recordset()

    @classmethod
    def get_dummy_subscription_requests_vals(cls, **custom_vals):
        vals = {
            "share_product_id": cls.share_y.id,
            "ordered_parts": 2,
            "firstname": "first name",
            "lastname": "last name",
            "email": "email@example.net",
            "phone": "dummy phone",
            "address": "dummy street",
            "zip_code": "dummy zip",
            "city": "dummy city",
            "country_id": cls.env.ref("base.be").id,
            "lang": "en_US",
            "gender": "other",
            "birthdate": "1980-01-01",
            "iban": "BE60096123456870",
            "source": "manual",
        }

        vals.update(custom_vals)
        return vals

    @classmethod
    def get_dummy_company_subscription_requests_vals(cls):
        vals = cls.get_dummy_subscription_requests_vals(
            is_company=True,
            company_name="dummy company",
            company_email="companyemail@example.net",
            company_register_number="dummy company register number",
            contact_person_function="dummy contact person function",
        )
        return vals

    @classmethod
    def create_dummy_subscription_request(cls):
        return cls.env["subscription.request"].create(
            cls.get_dummy_subscription_requests_vals()
        )

    @classmethod
    def create_dummy_company_subscription_request(cls):
        return cls.env["subscription.request"].create(
            cls.get_dummy_company_subscription_requests_vals()
        )

    @classmethod
    def create_dummy_subscription_from_partner(cls, partner):
        vals = cls.get_dummy_subscription_requests_vals(partner_id=partner.id)
        return cls.env["subscription.request"].create(vals)

    @classmethod
    def create_dummy_subscription_from_company_partner(cls, partner):
        vals = cls.get_dummy_company_subscription_requests_vals()
        vals["partner_id"] = partner.id
        return cls.env["subscription.request"].create(vals)

    @classmethod
    def validate_subscription_request_and_pay(cls, subscription_request):
        subscription_request.validate_subscription_request()
        # Ensure the invoice exists before attempting to pay it
        if subscription_request.capital_release_request:
            cls.pay_invoice(
                subscription_request.capital_release_request, force_payment=True
            )
        else:
            raise ValueError("Capital release invoice was not generated.")

    @classmethod
    def create_dummy_cooperator(cls):
        subscription_request = cls.create_dummy_subscription_request()
        cls.validate_subscription_request_and_pay(subscription_request)
        return subscription_request.partner_id

    @classmethod
    def create_dummy_company_cooperator(cls):
        subscription_request = cls.create_dummy_company_subscription_request()
        cls.validate_subscription_request_and_pay(subscription_request)
        return subscription_request.partner_id
