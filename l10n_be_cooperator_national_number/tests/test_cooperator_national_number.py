# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from unittest import mock

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase

from odoo.addons.cooperator.tests.cooperator_test_mixin import CooperatorTestMixin

NATIONAL_NUMBER = 90010100123

account_move_action_post = (
    "odoo.addons.account.models.account_move.AccountMove.action_post"
)


class TestCooperatorNationalNumber(TransactionCase, CooperatorTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_up_cooperator_test_data()

    def create_subscription_request(self):
        vals = self.get_dummy_subscription_requests_vals()
        return self.env["subscription.request"].create(vals)

    def set_national_number_required(self):
        self.company.display_national_number = True
        self.company.require_national_number = True

    def test_require_without_display(self):
        """You cannot require a national number without also displaying it."""
        self.company.write(
            {
                "display_national_number": False,
                "require_national_number": False,
            }
        )
        with self.assertRaises(ValidationError):
            self.company.require_national_number = True
        self.set_national_number_required()
        with self.assertRaises(ValidationError):
            self.company.display_national_number = False

    def test_company_not_required(self):
        """Subscription requests for companies do not require a national number."""
        self.set_national_number_required()
        vals = self.get_dummy_company_subscription_requests_vals()
        subscription_request = self.env["subscription.request"].create(vals)
        subscription_request.validate_subscription_request()
        self.assertFalse(subscription_request.display_national_number)
        self.assertFalse(subscription_request.require_national_number)

    def test_national_number_applied_to_partner(self):
        self.set_national_number_required()
        subscription_request = self.create_subscription_request()
        subscription_request.national_number = NATIONAL_NUMBER
        subscription_request.validate_subscription_request()
        partner = subscription_request.partner_id
        created_id_number = self.env["res.partner.id_number"].search(
            [("name", "=", NATIONAL_NUMBER)]
        )
        self.assertTrue(created_id_number)
        self.assertEqual(created_id_number.partner_id, partner)

    def test_error_if_missing_and_required(self):
        self.set_national_number_required()
        subscription_request = self.create_subscription_request()
        with self.assertRaises(UserError):
            subscription_request.validate_subscription_request()

    def test_no_national_number_provided(self):
        """Expect an error if no national number is given, but one is required."""
        self.set_national_number_required()
        vals = self.get_dummy_subscription_requests_vals()
        subscription_request = self.env["subscription.request"].create(vals)
        with self.assertRaises(UserError):
            subscription_request.validate_subscription_request()

    @mock.patch(account_move_action_post)
    def test_invalid_national_number_provided(self, account_move_action_post_mock):
        """
        Providing an invalid national number should raise a validation error.
        """
        self.set_national_number_required()
        vals = self.get_dummy_subscription_requests_vals()
        subscription_request = self.env["subscription.request"].create(vals)
        subscription_request.national_number = "42"
        with self.assertRaises(ValidationError):
            subscription_request.validate_subscription_request()
        # no capital release requests should be created or posted
        capital_release_requests = self.env["account.move"].search(
            [("subscription_request", "=", subscription_request.id)]
        )
        self.assertFalse(capital_release_requests)
        # mocking account.move.create() would be better, but if it is called,
        # the error is confusing: psycopg2.ProgrammingError: can't adapt type
        # 'MagicMock'
        account_move_action_post_mock.assert_not_called()

    def test_national_number_provided_not_required(self):
        """Expect no error when a number is given but not required."""
        vals = self.get_dummy_subscription_requests_vals()
        subscription_request = self.env["subscription.request"].create(vals)
        subscription_request.national_number = NATIONAL_NUMBER
        subscription_request.validate_subscription_request()

    def test_no_national_number_provided_not_required(self):
        """Expect no error when no number is given nor required."""
        vals = self.get_dummy_subscription_requests_vals()
        subscription_request = self.env["subscription.request"].create(vals)
        subscription_request.validate_subscription_request()
