# Copyright 2019 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import SavepointCase

from odoo.addons.cooperator.tests.cooperator_test_mixin import CooperatorTestMixin


class TestCooperatorNationalNumber(SavepointCase, CooperatorTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_up_cooperator_test_data()

    def create_subscription_request(self):
        vals = self.get_dummy_subscription_requests_vals()
        return self.env["subscription.request"].create(vals)

    def set_national_number_required(self):
        company = self.env.company
        company.display_national_number = True
        company.require_national_number = True

    def test_require_without_display(self):
        """You cannot require a national number without also displaying it."""
        company = self.env.company
        company.write(
            {
                "display_national_number": False,
                "require_national_number": False,
            }
        )
        with self.assertRaises(ValidationError):
            company.require_national_number = True
        self.set_national_number_required()
        with self.assertRaises(ValidationError):
            company.display_national_number = False

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
        id_number = 12345
        subscription_request.national_number = id_number
        subscription_request.validate_subscription_request()
        partner = subscription_request.partner_id
        created_id_number = self.env["res.partner.id_number"].search(
            [("name", "=", id_number)]
        )
        self.assertTrue(created_id_number)
        self.assertEqual(created_id_number.partner_id, partner)

    def test_error_if_missing_and_required(self):
        self.set_national_number_required()
        subscription_request = self.create_subscription_request()
        with self.assertRaises(UserError):
            subscription_request.validate_subscription_request()
