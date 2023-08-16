# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase

from .cooperator_test_mixin import CooperatorTestMixin


class TestCooperatorSecurity(TransactionCase, CooperatorTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_up_cooperator_test_data()
        cls.company_2 = cls.env["res.company"].create({"name": "Test Company"})
        cls.user_2 = cls.env["res.users"].create(
            {
                "name": "Test User",
                "login": "test@example.com",
                "company_id": cls.company_2.id,
                "company_ids": cls.company_2.ids,
            }
        )
        cls.env.ref("cooperator.cooperator_group_manager").write(
            {"users": [(4, cls.user_2.id)]}
        )

    def test_user_without_access(self):
        """A user that doesn't belong to the group cannot read cooperator
        records.
        """
        user_3 = self.env["res.users"].create(
            {
                "name": "Test User 3",
                "login": "test3@example.com",
                "company_id": self.company_2.id,
                "company_ids": self.company_2.ids,
            }
        )
        request = (
            self.env["subscription.request"]
            .with_company(self.company_2)
            .create(self.get_dummy_subscription_requests_vals())
        )
        request = request.with_user(user_3)
        # Write
        with self.assertRaises(AccessError):
            request.name = "foo"

    def test_access_own_records(self):
        """A user belonging to company_2 can access records belonging to that
        company.
        """
        request = (
            self.env["subscription.request"]
            .with_company(self.company_2)
            .create(self.get_dummy_subscription_requests_vals())
        )
        request = request.with_user(self.user_2)
        # Write
        request.name = "foo"
        # Read
        self.assertEqual(request.search([]), request)

    def test_subscription_request_multi_company(self):
        """When creating a subscription request for one company, a user of
        another company cannot use it.
        """
        request = self.env["subscription.request"].create(
            self.get_dummy_subscription_requests_vals()
        )
        request = request.with_user(self.user_2)
        # Write
        with self.assertRaises(AccessError):
            request.name = "foo"
        # Read
        self.assertFalse(request.search([]))
