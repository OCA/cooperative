# SPDX-FileCopyrightText: 2026 PopSolutions
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from datetime import date, timedelta

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged

from ..models.subscription_request import _lang_get as subscription_lang_get
from .cooperator_test_mixin import CooperatorTestMixin


@tagged("post_install", "-at_install")
class TestSubscriptionRequestGaps(TransactionCase, CooperatorTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_up_cooperator_test_data()

    def test_lang_get_lists_installed_languages(self):
        langs = subscription_lang_get(self.env["subscription.request"])
        self.assertIn("en_US", [code for code, _name in langs])

    def test_get_person_info_is_deprecated_alias(self):
        cooperator = self.create_dummy_cooperator()
        request = self.env["subscription.request"].new({})
        with self.assertWarns(DeprecationWarning):
            request.get_person_info(cooperator)
        self.assertEqual(request.email, cooperator.email)

    def test_onchange_partner_for_individual(self):
        cooperator = self.create_dummy_cooperator()
        request = self.env["subscription.request"].new({"partner_id": cooperator.id})
        request.onchange_partner()
        self.assertEqual(request.firstname, cooperator.firstname)
        self.assertEqual(request.email, cooperator.email)
        # a member subscribing again is an increase with a known iban
        self.assertEqual(request.type, "increase")
        self.assertEqual(request.iban, cooperator.bank_ids[0].acc_number)

    def test_onchange_partner_for_company(self):
        company_cooperator = self.create_dummy_company_cooperator()
        representative = company_cooperator.child_ids.filtered("representative")
        request = self.env["subscription.request"].new(
            {"partner_id": company_cooperator.id}
        )
        request.onchange_partner()
        self.assertTrue(request.is_company)
        self.assertEqual(request.company_name, company_cooperator.name)
        self.assertEqual(request.email, representative.email)

    def test_check_iban(self):
        request_model = self.env["subscription.request"]
        self.assertFalse(request_model.check_iban(False))
        self.assertFalse(request_model.check_iban("NOT_AN_IBAN"))
        self.assertTrue(request_model.check_iban("BE71096123456769"))

    def test_share_not_available_to_companies(self):
        self.share_y.by_company = False
        with self.assertRaises(ValidationError):
            self._create_company_request()

    def test_share_not_available_to_individuals(self):
        self.share_y.by_individual = False
        with self.assertRaises(ValidationError):
            self.create_dummy_subscription_request()

    def _create_company_request(self):
        vals = self.get_dummy_company_subscription_requests_vals()
        return self.env["subscription.request"].create(vals)

    def test_block_and_unblock_flow(self):
        request = self.create_dummy_subscription_request()
        request.block_subscription_request()
        self.assertEqual(request.state, "blocked")
        with self.assertRaises(ValidationError):
            request.block_subscription_request()
        request.unblock_subscription_request()
        self.assertEqual(request.state, "draft")
        with self.assertRaises(ValidationError):
            request.unblock_subscription_request()

    def test_cancel_from_cancelled_raises(self):
        request = self.create_dummy_subscription_request()
        request.cancel_subscription_request()
        with self.assertRaises(ValidationError):
            request.cancel_subscription_request()

    def test_put_on_waiting_list_twice_raises(self):
        self.company.send_waiting_list_email = True
        request = self.create_dummy_subscription_request()
        request.put_on_waiting_list()
        self.assertEqual(request.state, "waiting")
        with self.assertRaises(ValidationError):
            request.put_on_waiting_list()

    def test_company_representative_with_two_homonyms_raises(self):
        vals = self.get_dummy_company_subscription_requests_vals()
        for index in range(2):
            self.env["res.partner"].create(
                {
                    "firstname": f"Ambiguous{index}",
                    "lastname": "Person",
                    "email": vals["email"],
                }
            )
        request = self.env["subscription.request"].create(vals)
        with self.assertRaises(UserError):
            self.validate_subscription_request_and_pay(request)

    def test_company_representative_of_other_company_raises(self):
        other_company = self.env["res.partner"].create(
            {"name": "Other Company", "is_company": True}
        )
        vals = self.get_dummy_company_subscription_requests_vals()
        self.env["res.partner"].create(
            {
                "firstname": "Taken",
                "lastname": "Person",
                "email": vals["email"],
                "parent_id": other_company.id,
            }
        )
        request = self.env["subscription.request"].create(vals)
        with self.assertRaises(UserError):
            self.validate_subscription_request_and_pay(request)


@tagged("post_install", "-at_install")
class TestCooperativeMembershipGaps(TransactionCase, CooperatorTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_up_cooperator_test_data()
        cls.cooperator = cls.create_dummy_cooperator()
        cls.membership_model = cls.env["cooperative.membership"]

    def test_get_cooperator_from_email(self):
        membership = self.membership_model.get_cooperator_from_email(
            f"  {self.cooperator.email}  "
        )
        self.assertEqual(membership.partner_id, self.cooperator)

    def test_get_cooperator_from_blank_email(self):
        self.assertFalse(self.membership_model.get_cooperator_from_email("   "))
        self.assertFalse(self.membership_model.get_cooperator_from_email(False))

    def test_get_cooperator_from_unknown_email(self):
        self.assertFalse(
            self.membership_model.get_cooperator_from_email("nobody@example.org")
        )

    def test_get_cooperator_from_crn(self):
        company_cooperator = self.create_dummy_company_cooperator()
        crn = company_cooperator.company_register_number
        membership = self.membership_model.get_cooperator_from_crn(f" {crn} ")
        self.assertEqual(membership.partner_id, company_cooperator)

    def test_get_cooperator_from_blank_crn(self):
        self.assertFalse(self.membership_model.get_cooperator_from_crn("   "))
        self.assertFalse(self.membership_model.get_cooperator_from_crn(False))


@tagged("post_install", "-at_install")
class TestSubscriptionRegisterGaps(TransactionCase, CooperatorTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_up_cooperator_test_data()
        cls.cooperator = cls.create_dummy_cooperator()

    def test_read_group_totals_amount_and_drops_raw_fields(self):
        result = self.env["subscription.register"].read_group(
            [("partner_id", "=", self.cooperator.id)],
            ["share_unit_price", "register_number_operation", "total_amount_line"],
            ["partner_id"],
        )
        self.assertEqual(len(result), 1)
        register = self.env["subscription.register"].search(
            [("partner_id", "=", self.cooperator.id)]
        )
        self.assertEqual(
            result[0]["total_amount_line"],
            sum(register.mapped("total_amount_line")),
        )


@tagged("post_install", "-at_install")
class TestOperationRequestGaps(TransactionCase, CooperatorTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_up_cooperator_test_data()
        cls.cooperator = cls.create_dummy_cooperator()

    def _make_operation(self, **overrides):
        vals = {
            "operation_type": "convert",
            "partner_id": self.cooperator.id,
            "share_product_id": self.share_y.id,
            "share_to_product_id": self.share_x.id,
            "quantity": 2,
        }
        vals.update(overrides)
        return self.env["operation.request"].create(vals)

    def test_effective_date_cannot_be_in_the_future(self):
        with self.assertRaises(ValidationError):
            self._make_operation(effective_date=date.today() + timedelta(days=5))

    def test_state_transitions(self):
        operation = self._make_operation()
        operation.submit_operation()
        self.assertEqual(operation.state, "waiting")
        operation.refuse_operation()
        self.assertEqual(operation.state, "refused")
        operation.reset_to_draft()
        self.assertEqual(operation.state, "draft")
        operation.cancel_operation()
        self.assertEqual(operation.state, "cancelled")

    def test_convert_to_same_share_type_raises(self):
        operation = self._make_operation(share_to_product_id=self.share_y.id)
        with self.assertRaises(ValidationError):
            operation.submit_operation()

    def test_convert_partial_shares_raises(self):
        operation = self._make_operation(quantity=1)
        with self.assertRaises(ValidationError):
            operation.submit_operation()

    def test_transfer_to_company_share_not_by_company_raises(self):
        receiver = self.env["res.partner"].create(
            {"name": "Receiver Company", "is_company": True}
        )
        self.share_y.by_company = False
        operation = self._make_operation(
            operation_type="transfer",
            share_to_product_id=False,
            partner_id_to=receiver.id,
        )
        with self.assertRaises(ValidationError):
            operation.submit_operation()


@tagged("post_install", "-at_install")
class TestResCompanyGaps(TransactionCase, CooperatorTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_up_cooperator_test_data()

    def test_approval_onchanges_force_display(self):
        company = self.env["res.company"].new(
            {
                "data_policy_approval_required": True,
                "internal_rules_approval_required": True,
                "financial_risk_approval_required": True,
                "generic_rules_approval_required": True,
            }
        )
        company.onchange_data_policy_approval_required()
        company.onchange_internal_rules_approval_required()
        company.onchange_financial_risk_approval_required()
        company.onchange_generic_rules_approval_required()
        self.assertTrue(company.display_data_policy_approval)
        self.assertTrue(company.display_internal_rules_approval)
        self.assertTrue(company.display_financial_risk_approval)
        self.assertTrue(company.display_generic_rules_approval)

    def test_logo_url(self):
        self.assertTrue(self.company.logo_url.endswith("/logo.png"))

    def test_required_fields_follow_company_approval_flags(self):
        self.company.write(
            {
                "data_policy_approval_required": True,
                "internal_rules_approval_required": True,
                "financial_risk_approval_required": True,
                "generic_rules_approval_required": True,
            }
        )
        required = self.env["subscription.request"].get_required_field()
        for field in (
            "data_policy_approved",
            "internal_rules_approved",
            "financial_risk_approved",
            "generic_rules_approved",
        ):
            self.assertIn(field, required)


@tagged("post_install", "-at_install")
class TestResPartnerGaps(TransactionCase, CooperatorTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_up_cooperator_test_data()
        cls.cooperator = cls.create_dummy_cooperator()

    def test_report_filename_for_member(self):
        self.assertEqual(
            self.cooperator._get_report_base_filename(),
            f"Cooperator Certificate - {self.cooperator.name}",
        )

    def test_report_filename_for_non_member(self):
        partner = self.env["res.partner"].create({"name": "Someone"})
        self.assertEqual(partner._get_report_base_filename(), "unknown")

    def test_share_quantities_without_membership(self):
        partner = self.env["res.partner"].create({"name": "Someone"})
        self.assertFalse(dict(partner.get_share_quantities()))

    def test_onchange_parent_sets_representative(self):
        company_partner = self.env["res.partner"].create(
            {"name": "A Company", "is_company": True}
        )
        contact = self.env["res.partner"].new(
            {"name": "Contact", "parent_id": company_partner.id}
        )
        contact.onchange_parent_id()
        self.assertTrue(contact.representative)

    def test_invoice_report_excludes_capital_releases(self):
        report_model = self.env["account.invoice.report"]
        result = report_model.search([("partner_id", "=", self.cooperator.id)])
        self.assertFalse(result)


@tagged("post_install", "-at_install")
class TestSubscriptionRequestPartnerMatch(TransactionCase, CooperatorTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_up_cooperator_test_data()

    def test_partner_domain_without_email_is_none(self):
        request = self.env["subscription.request"].new({})
        self.assertIsNone(request._get_partner_domain())

    def test_already_cooperator_without_partner_raises(self):
        request = self.create_dummy_subscription_request()
        request.write({"already_cooperator": True, "partner_id": False})
        with self.assertRaises(UserError):
            request._find_or_create_partner()


@tagged("post_install", "-at_install")
class TestOperationRequestErrors(TransactionCase, CooperatorTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_up_cooperator_test_data()
        cls.cooperator = cls.create_dummy_cooperator()

    def test_sell_back_full_flow(self):
        operation = self.env["operation.request"].create(
            {
                "operation_type": "sell_back",
                "partner_id": self.cooperator.id,
                "share_product_id": self.share_y.id,
                "quantity": 1,
            }
        )
        operation.submit_operation()
        operation.approve_operation()
        operation.execute_operation()
        self.assertEqual(operation.state, "done")
        self.assertEqual(self.cooperator.number_of_share, 1)

    def test_share_type_not_owned_raises(self):
        operation = self.env["operation.request"].create(
            {
                "operation_type": "sell_back",
                "partner_id": self.cooperator.id,
                "share_product_id": self.share_x.id,
                "quantity": 1,
            }
        )
        with self.assertRaises(ValidationError):
            operation.submit_operation()

    def test_hand_over_more_than_owned_raises(self):
        operation = self.env["operation.request"].create(
            {
                "operation_type": "sell_back",
                "partner_id": self.cooperator.id,
                "share_product_id": self.share_y.id,
                "quantity": 99,
            }
        )
        with self.assertRaises(ValidationError):
            operation.submit_operation()

    def test_linked_subscription_request_must_be_operation(self):
        plain_request = self.create_dummy_subscription_request()
        with self.assertRaises(ValidationError):
            self.env["operation.request"].create(
                {
                    "operation_type": "sell_back",
                    "partner_id": self.cooperator.id,
                    "share_product_id": self.share_y.id,
                    "quantity": 1,
                    "subscription_request": [(6, 0, [plain_request.id])],
                }
            )

    def test_transfer_to_existing_member(self):
        vals = self.get_dummy_subscription_requests_vals()
        vals.update(
            {
                "email": "second.coop@example.net",
                "firstname": "Second",
                "lastname": "Cooperator",
            }
        )
        request = self.env["subscription.request"].create(vals)
        self.validate_subscription_request_and_pay(request)
        receiver = request.partner_id

        operation = self.env["operation.request"].create(
            {
                "operation_type": "transfer",
                "partner_id": self.cooperator.id,
                "partner_id_to": receiver.id,
                "share_product_id": self.share_y.id,
                "quantity": 2,
            }
        )
        operation.submit_operation()
        operation.approve_operation()
        operation.execute_operation()
        self.assertEqual(operation.state, "done")
        self.assertEqual(self.cooperator.number_of_share, 0)
