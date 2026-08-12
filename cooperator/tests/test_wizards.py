# SPDX-FileCopyrightText: 2026 PopSolutions
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from datetime import timedelta

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged

from ..models.share_type import get_share_types
from .cooperator_test_mixin import CooperatorTestMixin


@tagged("post_install", "-at_install")
class TestShareType(TransactionCase, CooperatorTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_up_cooperator_test_data()

    def test_get_share_types_lists_all_shares(self):
        share_types = get_share_types(self.env)
        codes = [code for code, _name in share_types]
        self.assertIn("share_x", codes)
        self.assertIn("share_y", codes)


@tagged("post_install", "-at_install")
class TestValidateSubscriptionRequestWizard(TransactionCase, CooperatorTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_up_cooperator_test_data()

    def test_validate_only_draft_and_waiting_requests(self):
        draft_request = self.create_dummy_subscription_request()
        waiting_request = self.create_dummy_subscription_request()
        waiting_request.put_on_waiting_list()
        cancelled_request = self.create_dummy_subscription_request()
        cancelled_request.cancel_subscription_request()

        wizard = (
            self.env["validate.subscription.request"]
            .with_context(
                active_ids=(draft_request | waiting_request | cancelled_request).ids
            )
            .create({})
        )
        self.assertTrue(wizard.validate())

        self.assertEqual(draft_request.state, "done")
        self.assertEqual(waiting_request.state, "done")
        self.assertEqual(cancelled_request.state, "cancelled")


@tagged("post_install", "-at_install")
class TestShareLineUpdateInfo(TransactionCase, CooperatorTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_up_cooperator_test_data()
        cls.cooperator = cls.create_dummy_cooperator()
        cls.share_line = cls.cooperator.share_ids[0]

    def _make_wizard(self):
        return (
            self.env["share.line.update.info"]
            .with_context(active_id=self.share_line.id)
            .create({"effective_date": self.share_line.effective_date})
        )

    def test_default_effective_date_comes_from_share_line(self):
        wizard = self._make_wizard()
        self.assertEqual(wizard.effective_date, self.share_line.effective_date)
        self.assertEqual(wizard.share_line, self.share_line)
        self.assertEqual(wizard.cooperator, self.cooperator)

    def test_update_changes_line_and_register_dates(self):
        new_date = self.share_line.effective_date + timedelta(days=7)
        register = self.env["subscription.register"].search(
            [
                ("partner_id", "=", self.cooperator.id),
                ("share_product_id", "=", self.share_line.share_product_id.id),
            ]
        )
        self.assertEqual(len(register), 1)

        wizard = self._make_wizard()
        wizard.effective_date = new_date
        self.assertTrue(wizard.update())

        self.assertEqual(self.share_line.effective_date, new_date)
        self.assertEqual(register.date, new_date)

    def test_update_with_ambiguous_register_raises(self):
        register = self.env["subscription.register"].search(
            [("partner_id", "=", self.cooperator.id)]
        )
        register.copy(
            {
                "name": "999",
                "register_number_operation": 999,
                "partner_id": self.cooperator.id,
                "date": self.share_line.effective_date,
                "quantity": self.share_line.share_number,
                "share_product_id": self.share_line.share_product_id.id,
            }
        )
        wizard = self._make_wizard()
        wizard.effective_date = self.share_line.effective_date + timedelta(days=1)
        with self.assertRaises(UserError):
            wizard.update()


@tagged("post_install", "-at_install")
class TestPartnerCreateSubscription(TransactionCase, CooperatorTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_up_cooperator_test_data()
        cls.wizard_model = cls.env["partner.create.subscription"]

    def _make_wizard(self, partner, **vals):
        model = self.wizard_model.with_context(active_id=partner.id)
        base_vals = {"share_qty": 1}
        if not partner.bank_ids:
            base_vals["bank_account"] = "BE71096123456769"
        base_vals.update(vals)
        return model.create(base_vals)

    def test_defaults_for_individual_partner(self):
        cooperator = self.create_dummy_cooperator()
        wizard = self._make_wizard(cooperator)
        self.assertFalse(wizard.is_company)
        self.assertEqual(wizard.cooperator, cooperator)
        self.assertEqual(wizard.email, cooperator.email)
        self.assertEqual(wizard.share_product.default_share_product, True)

    def test_subscription_amount_is_price_times_quantity(self):
        cooperator = self.create_dummy_cooperator()
        wizard = self._make_wizard(cooperator, share_qty=3)
        self.assertEqual(
            wizard.subscription_amount, wizard.share_product.list_price * 3
        )

    def test_onchange_share_type_sets_minimum_quantity(self):
        cooperator = self.create_dummy_cooperator()
        self.share_x.minimum_quantity = 5
        wizard = self._make_wizard(cooperator)
        wizard.share_product = self.share_x
        wizard.on_change_share_type()
        self.assertEqual(wizard.share_qty, 5)

    def test_no_default_share_product_raises(self):
        cooperator = self.create_dummy_cooperator()
        # demo data may define its own default share products
        self.env["product.product"].search(
            [("default_share_product", "=", True)]
        ).write({"default_share_product": False})
        with self.assertRaises(UserError):
            self._make_wizard(cooperator)

    def test_create_subscription_for_individual(self):
        cooperator = self.create_dummy_cooperator()
        wizard = self._make_wizard(cooperator, share_qty=2)
        action = wizard.create_subscription()

        request = self.env["subscription.request"].browse(action["res_id"])
        self.assertEqual(request.partner_id, cooperator)
        self.assertEqual(request.ordered_parts, 2)
        self.assertEqual(request.firstname, cooperator.firstname)
        self.assertEqual(request.source, "crm")
        self.assertEqual(request.iban, wizard.bank_account)

    def test_create_subscription_creates_bank_account_when_missing(self):
        cooperator = self.create_dummy_cooperator()
        cooperator.bank_ids.unlink()
        wizard = self._make_wizard(cooperator)
        wizard.create_subscription()
        self.assertEqual(
            cooperator.bank_ids.sanitized_acc_number,
            wizard.bank_account.replace(" ", ""),
        )

    def test_create_subscription_backfills_partner_email(self):
        cooperator = self.create_dummy_cooperator()
        cooperator.email = False
        wizard = self._make_wizard(cooperator, email="backfill@example.org")
        wizard.create_subscription()
        self.assertEqual(cooperator.email, "backfill@example.org")

    def test_defaults_for_company_partner(self):
        company_cooperator = self.create_dummy_company_cooperator()
        representative = company_cooperator.child_ids.filtered("representative")
        wizard = self._make_wizard(company_cooperator)
        self.assertTrue(wizard.is_company)
        self.assertEqual(wizard.representative_email, representative.email)
        self.assertEqual(wizard.representative_firstname, representative.firstname)

    def test_create_subscription_for_company_uses_representative(self):
        company_cooperator = self.create_dummy_company_cooperator()
        representative = company_cooperator.child_ids.filtered("representative")
        wizard = self._make_wizard(company_cooperator, share_qty=1)
        action = wizard.create_subscription()

        request = self.env["subscription.request"].browse(action["res_id"])
        self.assertTrue(request.is_company)
        self.assertEqual(request.company_name, company_cooperator.name)
        self.assertEqual(request.email, representative.email)
        # the display name of a company request is the company name
        self.assertEqual(request.name, company_cooperator.name)

    def test_create_subscription_links_loose_representative(self):
        company_cooperator = self.create_dummy_company_cooperator()
        company_cooperator.child_ids.filtered("representative").unlink()
        loose_partner = self.env["res.partner"].create(
            {
                "firstname": "Loose",
                "lastname": "Contact",
                "email": "loose@example.org",
            }
        )
        wizard = self._make_wizard(
            company_cooperator,
            representative_email="loose@example.org",
            representative_firstname="Loose",
            representative_lastname="Contact",
        )
        action = wizard.create_subscription()
        self.assertEqual(loose_partner.parent_id, company_cooperator)
        request = self.env["subscription.request"].browse(action["res_id"])
        self.assertTrue(request.is_company)
        self.assertTrue(loose_partner.representative)

    def test_create_subscription_creates_new_representative(self):
        company_cooperator = self.create_dummy_company_cooperator()
        company_cooperator.child_ids.filtered("representative").unlink()
        wizard = self._make_wizard(
            company_cooperator,
            representative_email="new.rep@example.org",
            representative_firstname="New",
            representative_lastname="Rep",
        )
        wizard.create_subscription()
        representative = company_cooperator.child_ids.filtered("representative")
        self.assertEqual(representative.email, "new.rep@example.org")

    def _create_other_company_cooperator(self):
        vals = self.get_dummy_company_subscription_requests_vals()
        vals.update(
            {
                "company_name": "other company",
                "company_email": "othercompany@example.net",
                "company_register_number": "2222222222",
                "email": "other.rep@example.net",
            }
        )
        request = self.env["subscription.request"].create(vals)
        self.validate_subscription_request_and_pay(request)
        return request.partner_id

    def test_representative_of_other_company_raises(self):
        first_company = self.create_dummy_company_cooperator()
        second_company = self._create_other_company_cooperator()
        self.assertNotEqual(first_company, second_company)
        second_company.child_ids.filtered("representative").unlink()
        representative = first_company.child_ids.filtered("representative")

        wizard = self._make_wizard(
            second_company,
            representative_email=representative.email,
            representative_firstname=representative.firstname,
            representative_lastname=representative.lastname,
        )
        with self.assertRaises(UserError):
            wizard.create_subscription()

    def test_duplicate_representative_email_raises(self):
        company_cooperator = self.create_dummy_company_cooperator()
        company_cooperator.child_ids.filtered("representative").unlink()
        for index in range(2):
            self.env["res.partner"].create(
                {
                    "firstname": f"Dup{index}",
                    "lastname": "Contact",
                    "email": "dup@example.org",
                }
            )
        wizard = self._make_wizard(
            company_cooperator,
            representative_email="dup@example.org",
            representative_firstname="Dup",
            representative_lastname="Contact",
        )
        with self.assertRaises(UserError):
            wizard.create_subscription()
