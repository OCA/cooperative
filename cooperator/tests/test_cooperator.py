# SPDX-FileCopyrightText: 2019 Coop IT Easy SC
# SPDX-FileContributor: Robin Keunen <robin@coopiteasy.be>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from datetime import date, datetime, timedelta

from freezegun import freeze_time

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests.common import TransactionCase, users

from .cooperator_test_mixin import CooperatorTestMixin


class CooperatorCase(TransactionCase, CooperatorTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_up_cooperator_test_data()
        cls.share_line = cls.env["share.line"].create(
            {
                "share_product_id": cls.share_x.id,
                "share_number": 2,
                "share_unit_price": 50,
                "partner_id": cls.demo_partner.id,
                "effective_date": datetime.now() - timedelta(days=120),
            }
        )
        cls.company_2 = cls.create_company("company 2")

    @users("user-cooperator")
    def test_put_on_waiting_list(self):
        self.subscription_request_1.put_on_waiting_list()
        self.assertEqual(self.subscription_request_1.state, "waiting")

    @users("user-cooperator")
    def test_validate_subscription_request(self):
        self.subscription_request_1.validate_subscription_request()

        self.assertEqual(self.subscription_request_1.state, "done")
        self.assertTrue(self.subscription_request_1.partner_id)
        self.assertTrue(self.subscription_request_1.partner_id.coop_candidate)
        self.assertFalse(self.subscription_request_1.partner_id.member)
        self.assertEqual(self.subscription_request_1.type, "new")
        self.assertTrue(len(self.subscription_request_1.capital_release_request) >= 1)
        self.assertEqual(
            self.subscription_request_1.capital_release_request.state, "posted"
        )

    @users("user-cooperator")
    def test_capital_release_request_name(self):
        self.subscription_request_1.validate_subscription_request()
        invoice = self.subscription_request_1.capital_release_request
        self.assertEqual(
            invoice.name,
            "SUBJ/{year}/001".format(year=date.today().year),
        )

    @users("user-cooperator")
    def test_capital_release_request_reversal_name(self):
        self.validate_subscription_request_and_pay(self.subscription_request_1)
        invoice = self.subscription_request_1.capital_release_request
        reverse_wizard = self.env["account.move.reversal"].create(
            {
                "move_ids": [fields.Command.link(invoice.id)],
                "reason": "test move reversal",
                "refund_method": "refund",
                "journal_id": invoice.journal_id.id,
            }
        )
        action = reverse_wizard.reverse_moves()
        reversed_move = self.env["account.move"].browse(action["res_id"])
        self.assertEqual(
            reversed_move.name,
            "RSUBJ/{year}/001".format(year=date.today().year),
        )
        self.assertTrue(reversed_move.release_capital_request)

    @users("user-cooperator")
    def test_register_payment_for_capital_release(self):
        self.validate_subscription_request_and_pay(self.subscription_request_1)
        invoice = self.subscription_request_1.capital_release_request
        self.assertEqual(invoice.state, "posted")

        partner = self.subscription_request_1.partner_id
        self.assertFalse(partner.coop_candidate)
        self.assertTrue(partner.member)
        self.assertTrue(partner.share_ids)
        self.assertEqual(partner.effective_date, fields.Date.today())

        share = partner.share_ids[0]
        self.assertEqual(share.share_number, self.subscription_request_1.ordered_parts)
        self.assertEqual(
            share.share_product_id, self.subscription_request_1.share_product_id
        )
        self.assertEqual(share.effective_date, fields.Date.today())

    @users("user-cooperator")
    def test_effective_date_from_payment_date(self):
        self.subscription_request_1.validate_subscription_request()
        invoice = self.subscription_request_1.capital_release_request
        self.pay_invoice(invoice, date(2022, 6, 21))

        partner = self.subscription_request_1.partner_id
        self.assertEqual(partner.effective_date, date(2022, 6, 21))

    @users("user-cooperator")
    def test_pay_invoice_sets_effective(self):
        self.subscription_request_1.validate_subscription_request()
        partner = self.subscription_request_1.partner_id
        membership = partner.cooperative_membership_id
        self.assertFalse(membership.member)
        self.assertFalse(membership.cooperator_register_number)
        self.assertFalse(membership.partner_id.user_ids)
        # Make sure to create a user.
        self.env.company.sudo().create_user = True

        invoice = self.subscription_request_1.capital_release_request
        self.pay_invoice(invoice, date(2022, 6, 21))

        self.assertTrue(membership.member)
        self.assertFalse(membership.old_member)
        self.assertTrue(membership.cooperator_register_number)
        self.assertTrue(membership.partner_id.user_ids)
        self.assertEqual(membership.partner_id.user_ids.company_id, self.env.company)
        self.assertEqual(membership.partner_id.user_ids.company_ids, self.env.company)

    @users("user-cooperator")
    def test_effective_date_from_account_move_date(self):
        # the effective date should also work with an account.move without an
        # account.payment.
        self.subscription_request_1.validate_subscription_request()
        invoice = self.subscription_request_1.capital_release_request
        self.create_payment_account_move(invoice, date(2022, 6, 21))
        partner = self.subscription_request_1.partner_id
        self.assertEqual(partner.effective_date, date(2022, 6, 21))

    @users("user-cooperator")
    def test_effective_date_from_multiple_moves(self):
        # the effective date should come from the most recent account.move.
        self.subscription_request_1.validate_subscription_request()
        invoice = self.subscription_request_1.capital_release_request
        amount = invoice.line_ids[0].credit / 2
        self.create_payment_account_move(invoice, date(2022, 6, 18), amount)
        self.create_payment_account_move(invoice, date(2022, 6, 21), amount)
        partner = self.subscription_request_1.partner_id
        self.assertEqual(partner.effective_date, date(2022, 6, 21))

    @users("demo")
    def test_user_access_rules(self):
        user_demo = self.env.ref("base.user_demo")
        # class object was loaded with root user and its rights
        # so we need to reload it with demo user rights
        request_as_user = self.subscription_request_1.with_user(user_demo)
        with self.assertRaises(AccessError):
            request_as_user.name = "test write request"
        with self.assertRaises(AccessError):
            create_values = self.get_dummy_subscription_requests_vals()
            self.env["subscription.request"].create(create_values)
        with self.assertRaises(AccessError):
            request_as_user.unlink()

        share_line_as_user = self.share_line.with_user(user_demo)
        with self.assertRaises(AccessError):
            share_line_as_user.share_number = 3

    @users("user-cooperator")
    def test_cooperator_access_rules(self):
        cooperator_user = self.ref("cooperator.res_users_user_cooperator_demo")
        # cf comment in test_user_access_rules
        resquest_as_cooperator = self.subscription_request_1.with_user(cooperator_user)
        resquest_as_cooperator.name = "test write request"
        create_values = self.get_dummy_subscription_requests_vals()
        create_request = self.env["subscription.request"].create(create_values)
        with self.assertRaises(AccessError):
            create_request.unlink()

        share_line_as_cooperator_user = self.share_line.with_user(cooperator_user)
        share_line_as_cooperator_user.share_number = 3
        with self.assertRaises(AccessError):
            share_line_as_cooperator_user.unlink()

        share_type_as_cooperator_user = self.share_x.with_user(cooperator_user)
        share_type_as_cooperator_user.list_price = 30
        with self.assertRaises(AccessError):
            self.env["product.template"].create(
                {
                    "name": "Part C - Client",
                    "short_name": "Part C",
                    "is_share": True,
                    "list_price": 50,
                }
            )
        with self.assertRaises(AccessError):
            share_type_as_cooperator_user.unlink()

    @users("manager-cooperator")
    def test_cooperator_manager_access_rules(self):
        cooperator_manager = self.ref("cooperator.res_users_manager_cooperator_demo")
        # cf comment in test_user_access_rules
        request_as_cooperator_manager = self.subscription_request_1.with_user(
            cooperator_manager
        )
        request_as_cooperator_manager.name = "test write request"
        create_values = self.get_dummy_subscription_requests_vals()
        create_request = self.env["subscription.request"].create(create_values)
        with self.assertRaises(AccessError):
            create_request.unlink()

        share_type = self.env["product.template"].create(
            {
                "name": "Part C - Client",
                "short_name": "Part C",
                "is_share": True,
                "list_price": 50,
            }
        )
        share_type.list_price = 30
        share_type.unlink()

    def test_compute_is_valid_iban_on_subscription_request(self):
        self.subscription_request_1.iban = False
        self.subscription_request_1.skip_iban_control = False

        # empty iban - don't skip
        self.assertFalse(self.subscription_request_1.is_valid_iban)

        # good iban - don't skip
        self.subscription_request_1.iban = "BE71096123456769"
        self.assertTrue(self.subscription_request_1.is_valid_iban)

        # wrong iban - don't skip
        self.subscription_request_1.iban = "xxxx"
        self.assertFalse(self.subscription_request_1.is_valid_iban)

        # wrong iban - don't skip
        self.subscription_request_1.iban = "BE71096123456760"
        self.assertFalse(self.subscription_request_1.is_valid_iban)

        # wrong iban - skip
        self.subscription_request_1.skip_iban_control = True
        self.assertTrue(self.subscription_request_1.is_valid_iban)

        # empty iban - skip
        self.subscription_request_1.iban = False
        self.assertTrue(self.subscription_request_1.is_valid_iban)

    def test_create_subscription_from_non_cooperator_partner(self):
        partner = self.env["res.partner"].create(
            {
                "name": "dummy partner 1",
            }
        )
        subscription_request = self.create_dummy_subscription_from_partner(partner)
        self.assertTrue(partner.cooperator)
        self.assertFalse(partner.coop_candidate)
        self.assertFalse(partner.member)
        subscription_request.validate_subscription_request()
        self.assertTrue(partner.cooperator)
        self.assertTrue(partner.coop_candidate)
        self.assertFalse(partner.member)
        self.pay_invoice(subscription_request.capital_release_request)
        self.assertTrue(partner.cooperator)
        self.assertFalse(partner.coop_candidate)
        self.assertTrue(partner.member)

    def test_create_subscription_from_non_cooperator_company_partner(self):
        partner = self.env["res.partner"].create(
            {
                "name": "dummy partner 1",
                "is_company": True,
            }
        )
        subscription_request = self.create_dummy_subscription_from_company_partner(
            partner
        )
        self.assertTrue(partner.cooperator)
        self.assertFalse(partner.coop_candidate)
        self.assertFalse(partner.member)
        subscription_request.validate_subscription_request()
        self.assertTrue(partner.cooperator)
        self.assertTrue(partner.coop_candidate)
        self.assertFalse(partner.member)
        self.pay_invoice(subscription_request.capital_release_request)
        self.assertTrue(partner.cooperator)
        self.assertFalse(partner.coop_candidate)
        self.assertTrue(partner.member)

    def test_create_multiple_subscriptions_from_non_cooperator_partner(self):
        """
        Test that creating a subscription from a partner that has no parts yet
        creates a subscription request with the correct type.
        """
        partner = self.env["res.partner"].create(
            {
                "name": "dummy partner 1",
            }
        )
        subscription_request = self.create_dummy_subscription_from_partner(partner)
        self.assertEqual(subscription_request.type, "new")
        subscription_request2 = self.create_dummy_subscription_from_partner(partner)
        self.assertEqual(subscription_request2.type, "increase")

    def test_create_multiple_subscriptions_from_non_cooperator_company_partner(self):
        """
        Test that creating a subscription from a company partner that has no
        parts yet creates a subscription request with the correct type.
        """
        partner = self.env["res.partner"].create(
            {
                "name": "dummy partner 1",
                "is_company": True,
            }
        )
        subscription_request = self.create_dummy_subscription_from_company_partner(
            partner
        )
        self.assertEqual(subscription_request.type, "new")
        subscription_request2 = self.create_dummy_subscription_from_company_partner(
            partner
        )
        self.assertEqual(subscription_request2.type, "increase")

    def test_create_subscription_from_cooperator_partner(self):
        """
        Test that creating a subscription from a cooperator partner creates a
        subscription request with the correct type.
        """
        partner = self.create_dummy_cooperator()
        subscription_request = self.create_dummy_subscription_from_partner(partner)
        self.assertEqual(subscription_request.type, "increase")

    def test_create_subscription_from_cooperator_company_partner(self):
        """
        Test that creating a subscription from a cooperator company partner
        creates a subscription request with the correct type.
        """
        partner = self.create_dummy_company_cooperator()
        subscription_request = self.create_dummy_subscription_from_company_partner(
            partner
        )
        self.assertEqual(subscription_request.type, "increase")

    def test_create_subscription_without_partner(self):
        subscription_request = self.env["subscription.request"].create(
            self.get_dummy_subscription_requests_vals()
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
        self.assertEqual(partner.country_id, self.browse_ref("base.be"))
        self.assertEqual(partner.lang, "en_US")
        self.assertEqual(partner.gender, "other")
        self.assertEqual(partner.birthdate_date, date(1980, 1, 1))
        self.assertTrue(partner.cooperator)

    def test_create_subscription_for_company_without_partner(self):
        vals = self.get_dummy_company_subscription_requests_vals()
        subscription_request = self.env["subscription.request"].create(vals)
        self.assertEqual(subscription_request.type, "new")
        self.assertEqual(subscription_request.name, "dummy company")
        self.assertFalse(subscription_request.partner_id)
        subscription_request.validate_subscription_request()
        partner = subscription_request.partner_id
        self.assertTrue(partner)
        self.assertTrue(partner.is_company)
        self.assertFalse(partner.firstname)
        self.assertEqual(partner.lastname, "dummy company")
        self.assertEqual(partner.name, "dummy company")
        self.assertEqual(partner.email, "companyemail@example.net")
        self.assertFalse(partner.phone)
        self.assertEqual(partner.street, "dummy street")
        self.assertEqual(partner.zip, "dummy zip")
        self.assertEqual(partner.city, "dummy city")
        self.assertEqual(partner.country_id, self.browse_ref("base.be"))
        self.assertEqual(partner.lang, "en_US")
        self.assertFalse(partner.gender)
        self.assertFalse(partner.birthdate_date)
        self.assertTrue(partner.cooperator)
        representative = partner.child_ids
        self.assertTrue(representative)
        self.assertFalse(representative.is_company)
        self.assertEqual(representative.type, "representative")
        self.assertEqual(representative.function, "dummy contact person function")
        self.assertEqual(representative.firstname, "first name")
        self.assertEqual(representative.lastname, "last name")
        self.assertEqual(representative.name, "first name last name")
        self.assertEqual(representative.email, "email@example.net")
        self.assertEqual(representative.phone, "dummy phone")
        self.assertEqual(representative.street, "dummy street")
        self.assertEqual(representative.zip, "dummy zip")
        self.assertEqual(representative.city, "dummy city")
        self.assertEqual(representative.country_id, self.browse_ref("base.be"))
        self.assertEqual(representative.lang, "en_US")
        self.assertEqual(representative.gender, "other")
        self.assertEqual(representative.birthdate_date, date(1980, 1, 1))
        # should this be true?
        self.assertTrue(representative.cooperator)

    def test_representative_of_member_company(self):
        vals = self.get_dummy_company_subscription_requests_vals()
        subscription_request = self.env["subscription.request"].create(vals)
        subscription_request.validate_subscription_request()
        partner = subscription_request.partner_id
        representative = partner.child_ids
        self.assertFalse(representative.representative_of_member_company)
        self.pay_invoice(subscription_request.capital_release_request)
        self.assertTrue(representative.representative_of_member_company)

    def test_create_subscription_with_matching_email(self):
        partner = self.env["res.partner"].create(
            {
                "name": "dummy partner 1",
                "email": "dummy@example.net",
            }
        )
        vals = self.get_dummy_subscription_requests_vals()
        vals["email"] = "dummy@example.net"
        subscription_request = self.env["subscription.request"].create(vals)
        self.assertEqual(subscription_request.partner_id, partner)

    def test_create_subscription_with_multiple_matching_email(self):
        self.env["res.partner"].create(
            {
                "name": "dummy partner 1",
                "email": "dummy@example.net",
            }
        )
        partner2 = self.env["res.partner"].create(
            {
                "name": "dummy partner 2",
                "email": "dummy@example.net",
            }
        )
        partner2.create_cooperative_membership(self.company)
        vals = self.get_dummy_subscription_requests_vals()
        vals["email"] = "dummy@example.net"
        subscription_request = self.env["subscription.request"].create(vals)
        # if there are multiple email matches, take the one that is a
        # cooperator.
        self.assertEqual(subscription_request.partner_id, partner2)

    def test_create_subscription_with_matching_empty_email(self):
        partner = self.env["res.partner"].create(
            {
                "name": "dummy partner 1",
                "email": "",
            }
        )
        vals = self.get_dummy_subscription_requests_vals()
        vals["email"] = ""
        subscription_request = self.env["subscription.request"].create(vals)
        self.assertNotEqual(subscription_request.partner_id, partner)

    def test_create_subscription_with_matching_space_email(self):
        partner = self.env["res.partner"].create(
            {
                "name": "dummy partner 1",
                "email": "",
            }
        )
        vals = self.get_dummy_subscription_requests_vals()
        vals["email"] = " "
        subscription_request = self.env["subscription.request"].create(vals)
        self.assertNotEqual(subscription_request.partner_id, partner)

    def test_create_subscription_with_matching_company_register_number(self):
        # create a dummy person partner to check that the match is not done by
        # email for companies.
        self.env["res.partner"].create(
            {
                "name": "dummy partner 1",
                "email": "dummy@example.net",
            }
        )
        company_partner = self.env["res.partner"].create(
            {
                "name": "dummy company",
                "email": "dummycompany@example.net",
                "company_register_number": "dummy company register number",
                "is_company": True,
            }
        )
        vals = self.get_dummy_company_subscription_requests_vals()
        vals["email"] = "dummy@example.net"
        subscription_request = self.env["subscription.request"].create(vals)
        partner = subscription_request.partner_id
        self.assertEqual(partner, company_partner)
        # no representative is created
        self.assertFalse(partner.child_ids)

    def test_create_subscription_with_multiple_matching_company_register_number(self):
        self.env["res.partner"].create(
            {
                "name": "dummy company 1",
                "email": "dummycompany@example.net",
                "company_register_number": "dummy company register number",
                "is_company": True,
            }
        )
        company_partner2 = self.env["res.partner"].create(
            {
                "name": "dummy company 2",
                "email": "dummycompany@example.net",
                "company_register_number": "dummy company register number",
                "is_company": True,
            }
        )
        company_partner2.create_cooperative_membership(self.company)
        company_partner2.cooperator = True
        vals = self.get_dummy_company_subscription_requests_vals()
        subscription_request = self.env["subscription.request"].create(vals)
        partner = subscription_request.partner_id
        # if there are multiple company register number matches, take the one
        # that is a cooperator.
        self.assertEqual(partner, company_partner2)

    def test_create_subscription_with_matching_empty_company_register_number(self):
        company_partner = self.env["res.partner"].create(
            {
                "name": "dummy company",
                "email": "dummycompany@example.net",
                "company_register_number": "",
                "is_company": True,
            }
        )
        vals = self.get_dummy_company_subscription_requests_vals()
        vals["company_register_number"] = ""
        subscription_request = self.env["subscription.request"].create(vals)
        partner = subscription_request.partner_id
        self.assertNotEqual(partner, company_partner)

    def test_create_subscription_with_matching_space_company_register_number(self):
        company_partner = self.env["res.partner"].create(
            {
                "name": "dummy company",
                "email": "dummycompany@example.net",
                "company_register_number": "",
                "is_company": True,
            }
        )
        vals = self.get_dummy_company_subscription_requests_vals()
        vals["company_register_number"] = " "
        subscription_request = self.env["subscription.request"].create(vals)
        partner = subscription_request.partner_id
        self.assertNotEqual(partner, company_partner)

    def test_create_subscription_with_matching_none_company_register_number(self):
        company_partner = self.env["res.partner"].create(
            {
                "name": "dummy company",
                "email": "dummycompany@example.net",
                "is_company": True,
            }
        )
        vals = self.get_dummy_company_subscription_requests_vals()
        del vals["company_register_number"]
        subscription_request = self.env["subscription.request"].create(vals)
        partner = subscription_request.partner_id
        self.assertNotEqual(partner, company_partner)

    def test_subscription_journal_per_company(self):
        """
        Test that creating a new company creates a new subscription journal
        for it.
        """
        company_1 = self.company
        company_2 = self.company_2
        self.assertTrue(company_2.subscription_journal_id)
        self.assertEqual(company_2.subscription_journal_id.company_id, company_2)
        self.assertNotEqual(
            company_1.subscription_journal_id, company_2.subscription_journal_id
        )

    def test_subscription_request_journal_per_company(self):
        company_1 = self.company
        company_2 = self.company_2
        subscription_request_1 = self.env["subscription.request"].create(
            self.get_dummy_subscription_requests_vals()
        )
        subscription_request_2 = (
            self.env["subscription.request"]
            .with_company(company_2)
            .create(self.get_dummy_subscription_requests_vals())
        )
        self.assertEqual(subscription_request_1.company_id, company_1)
        self.assertEqual(subscription_request_2.company_id, company_2)
        self.assertEqual(
            subscription_request_1.get_journal(), company_1.subscription_journal_id
        )
        self.assertEqual(
            subscription_request_2.get_journal(), company_2.subscription_journal_id
        )

    def test_create_subscription_request_with_share_of_different_company(self):
        """
        Test that creating a subscription request with a share (product)
        linked to a different company than the current one fails.
        """
        # link the share to a specific company (instead of it being shared
        # across all of them).
        self.share_y.company_id = self.company.id
        company_2 = self.company_2
        with self.assertRaises(UserError):
            self.env["subscription.request"].with_company(company_2).create(
                self.get_dummy_subscription_requests_vals()
            )

    def test_create_operation_request_with_share_of_different_company(self):
        """
        Test that creating an operation request with a share (product)
        linked to a different company than the current one fails.
        """
        # link the share to a specific company (instead of it being shared
        # across all of them).
        self.share_y.company_id = self.company.id
        company_2 = self.company_2
        vals = {
            "partner_id": self.demo_partner.id,
            "operation_type": "sell_back",
            "share_product_id": self.share_y.id,
            "quantity": 2,
        }
        with self.assertRaises(UserError):
            self.env["operation.request"].with_company(company_2).create(vals)
        vals.update(
            {
                "share_product_id": self.share_x.id,
                "share_to_product_id": self.share_y.id,
            }
        )
        with self.assertRaises(UserError):
            self.env["operation.request"].with_company(company_2).create(vals)

    def test_create_cooperator_for_other_company(self):
        """
        Test that creating a cooperator for a different company works and
        keeps data correctly separated per company.
        """
        company_2 = self.company_2
        subscription_request = (
            self.env["subscription.request"]
            .with_company(company_2)
            .create(self.get_dummy_subscription_requests_vals())
        )
        self.validate_subscription_request_and_pay(subscription_request)
        invoice = subscription_request.capital_release_request
        self.assertEqual(invoice.company_id, company_2)

        partner = subscription_request.partner_id.with_company(self.company)
        self.assertFalse(partner.coop_candidate)
        self.assertFalse(partner.member)
        # partner.share_ids contains all share lines across all companies
        self.assertTrue(partner.share_ids)
        # the cooperative membership (company-dependent) contains only the
        # share lines for the current company.
        self.assertFalse(partner.cooperative_membership_id.share_ids)
        partner = partner.with_company(company_2)
        self.assertFalse(partner.coop_candidate)
        self.assertTrue(partner.member)
        self.assertTrue(partner.cooperative_membership_id.share_ids)
        self.assertEqual(partner.share_ids, partner.cooperative_membership_id.share_ids)

    def test_create_cooperator_for_non_current_company(self):
        """
        Test that creating a cooperator for a different company than the
        current one works and keeps data correctly separated per company.
        """
        company_2 = self.company_2
        subscription_request_vals = self.get_dummy_subscription_requests_vals()
        subscription_request_vals["company_id"] = company_2.id
        subscription_request = self.env["subscription.request"].create(
            subscription_request_vals
        )
        subscription_request.validate_subscription_request()
        invoice = subscription_request.capital_release_request
        self.assertEqual(invoice.company_id, company_2)
        self.pay_invoice(invoice)
        partner = subscription_request.partner_id
        cooperative_membership = partner.cooperative_membership_ids
        self.assertEqual(cooperative_membership.company_id, company_2)
        self.assertNotEqual(cooperative_membership.cooperator_register_number, 0)
        partner = subscription_request.partner_id.with_company(self.company)
        self.assertFalse(partner.coop_candidate)
        self.assertFalse(partner.member)
        self.assertFalse(partner.cooperative_membership_id.share_ids)
        partner = partner.with_company(company_2)
        self.assertFalse(partner.coop_candidate)
        self.assertTrue(partner.member)
        self.assertTrue(partner.cooperative_membership_id.share_ids)
        self.assertEqual(partner.share_ids, partner.cooperative_membership_id.share_ids)

    def test_create_cooperator_and_user_for_other_company(self):
        """
        Test that creating a cooperator with its corresponding user for a
        different company works.
        """
        company_2 = self.company_2
        company_2.create_user = True
        subscription_request = (
            self.env["subscription.request"]
            .with_company(company_2)
            .create(self.get_dummy_subscription_requests_vals())
        )
        self.validate_subscription_request_and_pay(subscription_request)
        partner = subscription_request.partner_id
        user = self.env["res.users"].search([("partner_id", "=", partner.id)])
        self.assertEqual(user.company_id, company_2)
        self.assertEqual(user.company_ids, company_2)

    def test_create_cooperator_and_user_for_multiple_companies(self):
        """
        Test that creating a cooperator with its corresponding user for a
        different company works.
        """
        self.company.create_user = True
        subscription_request_1 = self.env["subscription.request"].create(
            self.get_dummy_subscription_requests_vals()
        )
        self.validate_subscription_request_and_pay(subscription_request_1)
        partner_1 = subscription_request_1.partner_id
        company_2 = self.company_2
        company_2.create_user = True
        subscription_request_2 = (
            self.env["subscription.request"]
            .with_company(company_2)
            .create(self.get_dummy_subscription_requests_vals())
        )
        self.validate_subscription_request_and_pay(subscription_request_2)
        partner_2 = subscription_request_2.partner_id
        self.assertEqual(partner_1, partner_2)
        user = self.env["res.users"].search([("partner_id", "=", partner_1.id)])
        self.assertEqual(user.company_id, self.company)
        self.assertEqual(user.company_ids, self.company | company_2)

    def test_partner_company_dependent_fields_without_membership(self):
        """
        Test that company-dependent fields on res.partner without a membership
        should have their default value.
        """
        partner = self.env["res.partner"].create(
            {
                "name": "dummy partner 1",
            }
        )
        # at creation, a partner must not have a cooperative membership.
        self.assertFalse(partner.cooperative_membership_id)
        self.assertFalse(partner.cooperative_membership_ids)

        # without a cooperative membership, all fields should have their
        # default value.
        self.assertFalse(partner.cooperator)
        self.assertFalse(partner.member)
        self.assertFalse(partner.coop_candidate)
        self.assertFalse(partner.old_member)
        self.assertEqual(partner.cooperator_register_number, 0)
        self.assertEqual(partner.number_of_share, 0)
        self.assertEqual(partner.total_value, 0)
        self.assertEqual(partner.cooperator_type, False)
        self.assertEqual(partner.effective_date, False)
        self.assertFalse(partner.data_policy_approved)
        self.assertFalse(partner.internal_rules_approved)
        self.assertFalse(partner.financial_risk_approved)
        self.assertFalse(partner.generic_rules_approved)

    def test_set_partner_company_dependent_fields_without_membership(self):
        """
        Test that setting company-dependent fields on res.partner without a
        membership should fail.
        """
        partner = self.env["res.partner"].create(
            {
                "name": "dummy partner 1",
            }
        )
        # without a cooperative membership, setting the fields should fail.
        with self.assertRaises(ValidationError):
            partner.cooperator = True
        with self.assertRaises(ValidationError):
            partner.member = True
        with self.assertRaises(ValidationError):
            partner.coop_candidate = True
        with self.assertRaises(ValidationError):
            partner.old_member = True
        with self.assertRaises(ValidationError):
            partner.cooperator_register_number = 1
        with self.assertRaises(ValidationError):
            partner.number_of_share = 1
        with self.assertRaises(ValidationError):
            partner.total_value = 4.2
        with self.assertRaises(ValidationError):
            partner.cooperator_type = "share_a"
        with self.assertRaises(ValidationError):
            partner.effective_date = date(2023, 6, 21)
        with self.assertRaises(ValidationError):
            partner.data_policy_approved = True
        with self.assertRaises(ValidationError):
            partner.internal_rules_approved = True
        with self.assertRaises(ValidationError):
            partner.financial_risk_approved = True
        with self.assertRaises(ValidationError):
            partner.generic_rules_approved = True

    @freeze_time("2023-06-21")
    def test_existing_partner_company_dependent_fields_with_membership(self):
        """
        Test that making a partner cooperator should create a cooperative
        membership for the company, and that computed field should have the
        same value as on the cooperative membership.
        """
        partner = self.env["res.partner"].create(
            {
                "name": "dummy partner 1",
            }
        )
        vals = self.get_dummy_subscription_requests_vals()
        vals.update(
            {
                "partner_id": partner.id,
                "data_policy_approved": True,
                "internal_rules_approved": True,
                "financial_risk_approved": True,
                "generic_rules_approved": True,
            }
        )
        subscription_request = self.env["subscription.request"].create(vals)
        self.validate_subscription_request_and_pay(subscription_request)
        self.assertTrue(partner.cooperative_membership_id)
        self.assertEqual(partner.cooperative_membership_id.company_id, self.company)
        self.assertEqual(
            partner.cooperative_membership_ids, partner.cooperative_membership_id
        )
        self.assertTrue(partner.cooperator)
        self.assertTrue(partner.member)
        self.assertFalse(partner.coop_candidate)
        self.assertFalse(partner.old_member)
        self.assertNotEqual(partner.cooperator_register_number, 0)
        self.assertEqual(partner.number_of_share, 2)
        self.assertEqual(partner.total_value, 50)
        self.assertEqual(partner.cooperator_type, "share_y")
        self.assertEqual(partner.effective_date, date(2023, 6, 21))
        # fixme: these should probably be true. see comment in
        # subscription.request.validate_subscription_request()
        self.assertFalse(partner.data_policy_approved)
        self.assertFalse(partner.internal_rules_approved)
        self.assertFalse(partner.financial_risk_approved)
        self.assertFalse(partner.generic_rules_approved)
        cooperative_membership = partner.cooperative_membership_id
        self.assertEqual(partner.cooperator, cooperative_membership.cooperator)
        self.assertEqual(partner.member, cooperative_membership.member)
        self.assertEqual(partner.coop_candidate, cooperative_membership.coop_candidate)
        self.assertEqual(partner.old_member, cooperative_membership.old_member)
        self.assertEqual(
            partner.cooperator_register_number,
            cooperative_membership.cooperator_register_number,
        )
        self.assertEqual(
            partner.number_of_share, cooperative_membership.number_of_share
        )
        self.assertEqual(partner.total_value, cooperative_membership.total_value)
        self.assertEqual(
            partner.cooperator_type, cooperative_membership.cooperator_type
        )
        self.assertEqual(partner.effective_date, cooperative_membership.effective_date)
        self.assertEqual(
            partner.data_policy_approved, cooperative_membership.data_policy_approved
        )
        self.assertEqual(
            partner.internal_rules_approved,
            cooperative_membership.internal_rules_approved,
        )
        self.assertEqual(
            partner.financial_risk_approved,
            cooperative_membership.financial_risk_approved,
        )
        self.assertEqual(
            partner.generic_rules_approved,
            cooperative_membership.generic_rules_approved,
        )

    @freeze_time("2023-06-21")
    def test_partner_company_dependent_fields_with_membership(self):
        """
        Test that creating a cooperator partner should create a cooperative
        membership for the company, and that computed field should have the
        same value as on the cooperative membership.
        """
        vals = self.get_dummy_subscription_requests_vals()
        vals.update(
            {
                "data_policy_approved": True,
                "internal_rules_approved": True,
                "financial_risk_approved": True,
                "generic_rules_approved": True,
            }
        )
        subscription_request = self.env["subscription.request"].create(vals)
        self.validate_subscription_request_and_pay(subscription_request)
        partner = subscription_request.partner_id
        self.assertTrue(partner.cooperative_membership_id)
        self.assertEqual(partner.cooperative_membership_id.company_id, self.company)
        self.assertTrue(partner.cooperator)
        self.assertTrue(partner.member)
        self.assertFalse(partner.coop_candidate)
        self.assertFalse(partner.old_member)
        self.assertNotEqual(partner.cooperator_register_number, 0)
        self.assertEqual(partner.number_of_share, 2)
        self.assertEqual(partner.total_value, 50)
        self.assertEqual(partner.cooperator_type, "share_y")
        self.assertEqual(partner.effective_date, date(2023, 6, 21))
        self.assertTrue(partner.data_policy_approved)
        self.assertTrue(partner.internal_rules_approved)
        self.assertTrue(partner.financial_risk_approved)
        self.assertTrue(partner.generic_rules_approved)
        cooperative_membership = partner.cooperative_membership_id
        self.assertEqual(partner.cooperator, cooperative_membership.cooperator)
        self.assertEqual(partner.member, cooperative_membership.member)
        self.assertEqual(partner.coop_candidate, cooperative_membership.coop_candidate)
        self.assertEqual(partner.old_member, cooperative_membership.old_member)
        self.assertEqual(
            partner.cooperator_register_number,
            cooperative_membership.cooperator_register_number,
        )
        self.assertEqual(
            partner.number_of_share, cooperative_membership.number_of_share
        )
        self.assertEqual(partner.total_value, cooperative_membership.total_value)
        self.assertEqual(
            partner.cooperator_type, cooperative_membership.cooperator_type
        )
        self.assertEqual(partner.effective_date, cooperative_membership.effective_date)
        self.assertEqual(
            partner.data_policy_approved, cooperative_membership.data_policy_approved
        )
        self.assertEqual(
            partner.internal_rules_approved,
            cooperative_membership.internal_rules_approved,
        )
        self.assertEqual(
            partner.financial_risk_approved,
            cooperative_membership.financial_risk_approved,
        )
        self.assertEqual(
            partner.generic_rules_approved,
            cooperative_membership.generic_rules_approved,
        )

    @freeze_time("2023-06-21")
    def test_set_partner_company_dependent_fields_with_membership(self):
        """
        Test that setting company-dependent fields on the partner should set
        them on the cooperative membership.
        """
        partner = self.create_dummy_cooperator()
        partner.cooperator = False
        self.assertFalse(partner.cooperator)
        partner.member = False
        self.assertFalse(partner.member)
        # fixme: as this is a computed field, this should fail
        partner.coop_candidate = True
        self.assertTrue(partner.coop_candidate)
        partner.old_member = True
        self.assertTrue(partner.old_member)
        # fixme: as this is a readonly field, this should fail
        partner.cooperator_register_number = 42
        self.assertEqual(partner.cooperator_register_number, 42)
        # fixme: as this is a computed field, this should fail
        partner.number_of_share = 7
        self.assertEqual(partner.number_of_share, 7)
        # fixme: as this is a computed field, this should fail
        partner.total_value = 100
        self.assertEqual(partner.total_value, 100)
        # fixme: as this is a computed field, this should fail
        partner.cooperator_type = "share_x"
        self.assertEqual(partner.cooperator_type, "share_x")
        # fixme: as this is a computed field, this should fail
        partner.effective_date = date(2023, 6, 28)
        self.assertEqual(partner.effective_date, date(2023, 6, 28))
        partner.data_policy_approved = True
        self.assertTrue(partner.data_policy_approved)
        partner.internal_rules_approved = True
        self.assertTrue(partner.internal_rules_approved)
        partner.financial_risk_approved = True
        self.assertTrue(partner.financial_risk_approved)
        partner.generic_rules_approved = True
        self.assertTrue(partner.generic_rules_approved)
        cooperative_membership = partner.cooperative_membership_id
        self.assertEqual(partner.cooperator, cooperative_membership.cooperator)
        self.assertEqual(partner.member, cooperative_membership.member)
        self.assertEqual(partner.coop_candidate, cooperative_membership.coop_candidate)
        self.assertEqual(partner.old_member, cooperative_membership.old_member)
        self.assertEqual(
            partner.cooperator_register_number,
            cooperative_membership.cooperator_register_number,
        )
        self.assertEqual(
            partner.number_of_share, cooperative_membership.number_of_share
        )
        self.assertEqual(partner.total_value, cooperative_membership.total_value)
        self.assertEqual(
            partner.cooperator_type, cooperative_membership.cooperator_type
        )
        self.assertEqual(partner.effective_date, cooperative_membership.effective_date)
        self.assertEqual(
            partner.data_policy_approved, cooperative_membership.data_policy_approved
        )
        self.assertEqual(
            partner.internal_rules_approved,
            cooperative_membership.internal_rules_approved,
        )
        self.assertEqual(
            partner.financial_risk_approved,
            cooperative_membership.financial_risk_approved,
        )
        self.assertEqual(
            partner.generic_rules_approved,
            cooperative_membership.generic_rules_approved,
        )

    @freeze_time("2023-06-21")
    def test_set_partner_company_dependent_fields_on_membership(self):
        """
        Test that setting fields on the cooperative membership should update
        the company-dependent fields on the partner.
        """
        partner = self.create_dummy_cooperator()
        cooperative_membership = partner.cooperative_membership_id
        cooperative_membership.cooperator = False
        self.assertFalse(partner.cooperator)
        cooperative_membership.member = False
        self.assertFalse(partner.member)
        # fixme: as this is a computed field, this should fail
        cooperative_membership.coop_candidate = True
        self.assertTrue(partner.coop_candidate)
        cooperative_membership.old_member = True
        self.assertTrue(partner.old_member)
        # fixme: as this is a readonly field, this should fail
        cooperative_membership.cooperator_register_number = 42
        self.assertEqual(partner.cooperator_register_number, 42)
        # fixme: as this is a computed field, this should fail
        cooperative_membership.number_of_share = 7
        self.assertEqual(partner.number_of_share, 7)
        # fixme: as this is a computed field, this should fail
        cooperative_membership.total_value = 100
        self.assertEqual(partner.total_value, 100)
        # fixme: as this is a computed field, this should fail
        cooperative_membership.cooperator_type = "share_x"
        self.assertEqual(partner.cooperator_type, "share_x")
        # fixme: as this is a computed field, this should fail
        cooperative_membership.effective_date = date(2023, 6, 28)
        self.assertEqual(partner.effective_date, date(2023, 6, 28))
        cooperative_membership.data_policy_approved = True
        self.assertTrue(partner.data_policy_approved)
        cooperative_membership.internal_rules_approved = True
        self.assertTrue(partner.internal_rules_approved)
        cooperative_membership.financial_risk_approved = True
        self.assertTrue(partner.financial_risk_approved)
        cooperative_membership.generic_rules_approved = True
        self.assertTrue(partner.generic_rules_approved)

    @freeze_time("2023-06-21")
    def test_company_dependent_fields_for_other_company(self):
        """
        Test that partner company-dependenty fields should have a different
        value per company.
        """
        partner = self.create_dummy_cooperator()
        self.assertTrue(partner.cooperative_membership_id)
        self.assertTrue(partner.member)

        # with another company, the partner should not have a
        # cooperative_membership_id.
        partner = partner.with_company(self.company_2)
        self.assertFalse(partner.cooperative_membership_id)

        # all fields should have their default value.
        self.assertFalse(partner.cooperator)
        self.assertFalse(partner.member)
        self.assertFalse(partner.coop_candidate)
        self.assertFalse(partner.old_member)
        self.assertEqual(partner.cooperator_register_number, 0)
        self.assertEqual(partner.number_of_share, 0)
        self.assertEqual(partner.total_value, 0)
        self.assertEqual(partner.cooperator_type, False)
        self.assertEqual(partner.effective_date, False)
        self.assertFalse(partner.data_policy_approved)
        self.assertFalse(partner.internal_rules_approved)
        self.assertFalse(partner.financial_risk_approved)
        self.assertFalse(partner.generic_rules_approved)

        # setting the fields should fail.
        with self.assertRaises(ValidationError):
            partner.cooperator = True
        with self.assertRaises(ValidationError):
            partner.member = True
        with self.assertRaises(ValidationError):
            partner.coop_candidate = True
        with self.assertRaises(ValidationError):
            partner.old_member = True
        with self.assertRaises(ValidationError):
            partner.cooperator_register_number = 1
        with self.assertRaises(ValidationError):
            partner.number_of_share = 1
        with self.assertRaises(ValidationError):
            partner.total_value = 4.2
        with self.assertRaises(ValidationError):
            partner.cooperator_type = "share_a"
        with self.assertRaises(ValidationError):
            partner.effective_date = date(2023, 6, 21)
        with self.assertRaises(ValidationError):
            partner.data_policy_approved = True
        with self.assertRaises(ValidationError):
            partner.internal_rules_approved = True
        with self.assertRaises(ValidationError):
            partner.financial_risk_approved = True
        with self.assertRaises(ValidationError):
            partner.generic_rules_approved = True

    def test_cooperative_membership_for_other_company(self):
        """
        Test that making a partner cooperator of another company should create
        a cooperative membership for that company.
        """
        company_2 = self.company_2
        subscription_request = (
            self.env["subscription.request"]
            .with_company(company_2)
            .create(self.get_dummy_subscription_requests_vals())
        )
        self.validate_subscription_request_and_pay(subscription_request)
        partner = subscription_request.partner_id
        self.assertTrue(partner.cooperative_membership_id)
        self.assertEqual(partner.cooperative_membership_id.company_id, company_2)
        self.assertFalse(partner.with_company(self.company).cooperative_membership_id)

    def test_capital_release_request_receivable_account(self):
        """
        Test that the receivable account of capital release requests is the
        cooperator account.
        """
        self.subscription_request_1.validate_subscription_request()
        invoice = self.subscription_request_1.capital_release_request
        self.assertEqual(
            invoice.line_ids[-1].account_id,
            invoice.company_id.property_cooperator_account,
        )

    def test_capital_release_request_taxes(self):
        """
        Test that no taxes are added on capital release requests.
        """
        self.subscription_request_1.validate_subscription_request()
        invoice = self.subscription_request_1.capital_release_request
        self.assertFalse(invoice.invoice_line_ids.tax_ids)
        self.assertEqual(len(invoice.line_ids), 2)

    def _get_last_register_id(self):
        return self.env["subscription.register"].search([], order="id desc", limit=1).id

    def _get_new_register_records(self, last_register_id):
        return self.env["subscription.register"].search([("id", ">", last_register_id)])

    def _get_last_register_sequence_value(self):
        register_sequence = self.env["ir.sequence"].search(
            [("code", "=", "register.operation"), ("company_id", "=", self.company.id)]
        )
        return register_sequence.number_next_actual - 1

    @freeze_time("2023-06-21")
    def test_transfer_operation(self):
        """
        Test that the share transfer operation works correctly.
        """
        cooperator = self.create_dummy_cooperator()
        subscription_request_vals = self.get_dummy_subscription_requests_vals()
        subscription_request_vals.update(
            {
                "firstname": "first name 2",
                "lastname": "last name 2",
                "email": "email2@example.net",
                "is_operation": True,
                "source": "operation",
            }
        )
        operation_request = self.env["operation.request"].create(
            {
                "operation_type": "transfer",
                "partner_id": cooperator.id,
                "share_product_id": self.share_y.id,
                "quantity": 1,
                "receiver_not_member": True,
                "subscription_request": [
                    fields.Command.create(subscription_request_vals)
                ],
            }
        )
        self.assertEqual(operation_request.subscription_request.state, "transfer")
        operation_request.submit_operation()
        operation_request.approve_operation()
        last_register_id = self._get_last_register_id()
        operation_request.execute_operation()
        self.assertEqual(cooperator.number_of_share, 1)
        new_cooperator = self.env["res.partner"].search(
            [("email", "=", "email2@example.net")]
        )
        self.assertTrue(new_cooperator.member)
        self.assertEqual(new_cooperator.number_of_share, 1)
        # the dummy subscription request should be set as done to avoid
        # validating it twice.
        self.assertEqual(operation_request.subscription_request.state, "done")
        register_entry = self._get_new_register_records(last_register_id)
        self.assertEqual(register_entry.partner_id, cooperator)
        self.assertEqual(register_entry.partner_id_to, new_cooperator)
        self.assertEqual(register_entry.quantity, 1)
        self.assertEqual(register_entry.share_product_id, self.share_y)
        self.assertEqual(register_entry.type, "transfer")
        self.assertEqual(register_entry.share_unit_price, self.share_y.list_price)
        self.assertEqual(register_entry.date, date(2023, 6, 21))
        seq_number = self._get_last_register_sequence_value()
        self.assertEqual(register_entry.name, str(seq_number))
        self.assertEqual(register_entry.register_number_operation, seq_number)

    @freeze_time("2023-06-21")
    def test_transfer_operation_existing_cooperator(self):
        """
        Test that the share transfer operation to an existing cooperator works
        correctly.
        """
        cooperator = self.create_dummy_cooperator()
        subscription_request_vals = self.get_dummy_subscription_requests_vals()
        subscription_request_vals.update(
            {
                "firstname": "first name 2",
                "lastname": "last name 2",
                "email": "email2@example.net",
            }
        )
        subscription_request = self.env["subscription.request"].create(
            subscription_request_vals
        )
        self.validate_subscription_request_and_pay(subscription_request)
        new_cooperator = self.env["res.partner"].search(
            [("email", "=", "email2@example.net")]
        )
        operation_request = self.env["operation.request"].create(
            {
                "operation_type": "transfer",
                "partner_id": cooperator.id,
                "partner_id_to": new_cooperator.id,
                "share_product_id": self.share_y.id,
                "quantity": 1,
            }
        )
        operation_request.submit_operation()
        operation_request.approve_operation()
        last_register_id = self._get_last_register_id()
        operation_request.execute_operation()
        self.assertEqual(cooperator.number_of_share, 1)
        self.assertEqual(new_cooperator.number_of_share, 3)
        register_entry = self._get_new_register_records(last_register_id)
        self.assertEqual(register_entry.partner_id, cooperator)
        self.assertEqual(register_entry.partner_id_to, new_cooperator)
        self.assertEqual(register_entry.quantity, 1)
        self.assertEqual(register_entry.share_product_id, self.share_y)
        self.assertEqual(register_entry.type, "transfer")
        self.assertEqual(register_entry.share_unit_price, self.share_y.list_price)
        self.assertEqual(register_entry.date, date(2023, 6, 21))
        seq_number = self._get_last_register_sequence_value()
        self.assertEqual(register_entry.name, str(seq_number))
        self.assertEqual(register_entry.register_number_operation, seq_number)

    @freeze_time("2023-06-21")
    def test_sell_back_operation(self):
        """
        Test that the sell back operation works correctly.
        """
        cooperator = self.create_dummy_cooperator()
        operation_request = self.env["operation.request"].create(
            {
                "operation_type": "sell_back",
                "partner_id": cooperator.id,
                "share_product_id": self.share_y.id,
                "quantity": 1,
            }
        )
        operation_request.submit_operation()
        operation_request.approve_operation()
        last_register_id = self._get_last_register_id()
        operation_request.execute_operation()
        self.assertEqual(cooperator.number_of_share, 1)
        register_entry = self._get_new_register_records(last_register_id)
        self.assertEqual(register_entry.partner_id, cooperator)
        self.assertFalse(register_entry.partner_id_to)
        self.assertEqual(register_entry.quantity, 1)
        self.assertEqual(register_entry.share_product_id, self.share_y)
        self.assertEqual(register_entry.type, "sell_back")
        self.assertEqual(register_entry.share_unit_price, self.share_y.list_price)
        self.assertEqual(register_entry.date, date(2023, 6, 21))
        seq_number = self._get_last_register_sequence_value()
        self.assertEqual(register_entry.name, str(seq_number))
        self.assertEqual(register_entry.register_number_operation, seq_number)
        self.assertTrue(cooperator.member)

    def test_sell_back_all_shares(self):
        """
        Test that selling back all shares results in the cooperator to not be
        a cooperator anymore.
        """
        cooperator = self.create_dummy_cooperator()
        operation_request = self.env["operation.request"].create(
            {
                "operation_type": "sell_back",
                "partner_id": cooperator.id,
                "share_product_id": self.share_y.id,
                "quantity": 2,
            }
        )
        operation_request.submit_operation()
        operation_request.approve_operation()
        operation_request.execute_operation()
        self.assertFalse(cooperator.member)
        self.assertTrue(cooperator.old_member)

    @freeze_time("2023-06-21")
    def test_convert_operation(self):
        """
        Test that the share conversion operation works correctly.
        """
        cooperator = self.create_dummy_cooperator()
        operation_request = self.env["operation.request"].create(
            {
                "operation_type": "convert",
                "partner_id": cooperator.id,
                "share_product_id": self.share_y.id,
                "share_to_product_id": self.share_x.id,
                "quantity": 2,
            }
        )
        operation_request.submit_operation()
        operation_request.approve_operation()
        last_register_id = self._get_last_register_id()
        operation_request.execute_operation()
        # share_x costs twice as much as share_y, so there is only one share
        self.assertEqual(cooperator.number_of_share, 1)
        self.assertEqual(cooperator.cooperator_type, "share_x")
        share_line = cooperator.share_ids
        self.assertEqual(share_line.share_product_id, self.share_x)
        self.assertEqual(share_line.share_number, 1)
        self.assertEqual(share_line.share_unit_price, self.share_x.list_price)
        register_entry = self._get_new_register_records(last_register_id)
        self.assertEqual(register_entry.partner_id, cooperator)
        self.assertFalse(register_entry.partner_id_to)
        self.assertEqual(register_entry.quantity, 2)
        self.assertEqual(register_entry.share_product_id, self.share_y)
        self.assertEqual(register_entry.share_to_product_id, self.share_x)
        self.assertEqual(register_entry.quantity_to, 1)
        self.assertEqual(register_entry.type, "convert")
        self.assertEqual(register_entry.share_unit_price, self.share_y.list_price)
        self.assertEqual(register_entry.date, date(2023, 6, 21))
        seq_number = self._get_last_register_sequence_value()
        self.assertEqual(register_entry.name, str(seq_number))
        self.assertEqual(register_entry.register_number_operation, seq_number)

    def test_company_and_representative_email_different(self):
        """
        Test that it is not possible to create a subscription request with
        the same email address for the company and the representative.
        """
        subscription_request_vals = self.get_dummy_company_subscription_requests_vals()
        subscription_request_vals["company_email"] = subscription_request_vals["email"]
        with self.assertRaises(ValidationError) as cm:
            self.env["subscription.request"].create(subscription_request_vals)
        self.assertEqual(
            str(cm.exception), "Email and Company Email must be different."
        )

    def test_company_type_to_legal_form(self):
        """
        Test that the value of the company_type field of subscription request
        is copied to the legal form field of the created partner.
        """
        subscription_request_vals = self.get_dummy_company_subscription_requests_vals()
        # an existing type cannot be used because they are only defined in
        # localization modules.
        subscription_request_model = self.env["subscription.request"]
        res_partner_model = self.env["res.partner"]
        subscription_request_company_type = subscription_request_model._fields[
            "company_type"
        ]
        subscription_request_company_types = subscription_request_company_type.selection
        subscription_request_company_type.selection = [("dummy_type", "Dummy Type")]
        res_partner_legal_form = res_partner_model._fields["legal_form"]
        res_partner_legal_forms = res_partner_legal_form.selection
        res_partner_legal_form.selection = [("dummy_type", "Dummy Type")]
        subscription_request_vals["company_type"] = "dummy_type"
        subscription_request = subscription_request_model.create(
            subscription_request_vals
        )
        self.validate_subscription_request_and_pay(subscription_request)
        self.assertEqual(subscription_request.partner_id.legal_form, "dummy_type")
        # restore previous values
        subscription_request_company_type.selection = subscription_request_company_types
        res_partner_legal_form.selection = res_partner_legal_forms

    def test_cooperator_register_number_sequence_per_company(self):
        """
        Test that the cooperator register number sequence is different per
        company.
        """
        company_1 = self.create_company("test company 1")
        company_2 = self.create_company("test company 2")
        subscription_request_vals = self.get_dummy_subscription_requests_vals()
        subscription_request_vals["company_id"] = company_1.id
        subscription_request = self.env["subscription.request"].create(
            subscription_request_vals
        )
        self.validate_subscription_request_and_pay(subscription_request)
        cooperator_1 = subscription_request.partner_id
        subscription_request_vals = self.get_dummy_subscription_requests_vals()
        subscription_request_vals["company_id"] = company_2.id
        subscription_request = self.env["subscription.request"].create(
            subscription_request_vals
        )
        self.validate_subscription_request_and_pay(subscription_request)
        cooperator_2 = subscription_request.partner_id
        # since both subscription requests use the same email address, the
        # partner should be the same.
        self.assertEqual(cooperator_1, cooperator_2)
        self.assertEqual(len(cooperator_1.cooperative_membership_ids), 2)
        cooperative_membership_1 = cooperator_1.cooperative_membership_ids[0]
        self.assertEqual(cooperative_membership_1.company_id, company_1)
        self.assertEqual(cooperative_membership_1.cooperator_register_number, 1)
        cooperative_membership_2 = cooperator_2.cooperative_membership_ids[1]
        self.assertEqual(cooperative_membership_2.company_id, company_2)
        self.assertEqual(cooperative_membership_2.cooperator_register_number, 1)

    def test_get_create_cooperative_membership_create(self):
        """Create a membership if one does not yet exist."""
        partner = self.env["res.partner"].create({"name": "Jane Doe"})
        membership = partner.get_create_cooperative_membership(self.env.company)
        self.assertTrue(membership)

    def test_get_create_cooperative_membership_get(self):
        """Get the membership if one exists."""
        partner = self.env["res.partner"].create({"name": "Jane Doe"})
        partner.create_cooperative_membership(self.env.company)
        expected = partner.get_cooperative_membership(self.env.company)
        result = partner.get_create_cooperative_membership(self.env.company)
        self.assertEqual(result, expected)

    def test_set_effective(self):
        """Expect set_effective to do the things it says it does."""
        partner = self.env["res.partner"].create(
            {"name": "Jane Doe", "email": "jane@example.com"}
        )
        membership = partner.create_cooperative_membership(self.env.company)
        self.assertFalse(membership.member)
        self.assertFalse(membership.cooperator_register_number)
        self.assertFalse(membership.partner_id.user_ids)
        # Falsely set this to True.
        membership.old_member = True
        # Make sure to create a user.
        self.env.company.create_user = True
        membership.set_effective()
        self.assertTrue(membership.member)
        self.assertFalse(membership.old_member)
        self.assertTrue(membership.cooperator_register_number)
        self.assertTrue(membership.partner_id.user_ids)
        self.assertEqual(membership.partner_id.user_ids.company_id, self.env.company)
        self.assertEqual(membership.partner_id.user_ids.company_ids, self.env.company)

    def test_create_user_inactive(self):
        """When creating a user that is inactive, set it active and replace the
        companies.
        """
        partner = self.env["res.partner"].create(
            {"name": "Jane Doe", "email": "jane@example.com"}
        )
        other_company = self.env["res.company"].create({"name": "Foo Company"})
        user = self.env["res.users"].create(
            {
                "partner_id": partner.id,
                "login": partner.email,
                "company_id": other_company.id,
                "company_ids": [fields.Command.set([other_company.id])],
            }
        )
        user.active = False
        membership = partner.create_cooperative_membership(self.env.company)
        membership.create_user()
        new_user = self.env["res.users"].search([("login", "=", "jane@example.com")])
        self.assertEqual(new_user, user)
        self.assertEqual(user.company_id, self.env.company)
        self.assertEqual(user.company_ids, self.env.company)

    def test_create_user_new_company(self):
        """If calling create_user for a user that already exists, but which
        doesn't belong to the membership's company yet, add the company.
        """
        partner = self.env["res.partner"].create(
            {"name": "Jane Doe", "email": "jane@example.com"}
        )
        other_company = self.env["res.company"].create({"name": "Foo Company"})
        user = self.env["res.users"].create(
            {
                "partner_id": partner.id,
                "login": partner.email,
                "company_id": other_company.id,
                "company_ids": [fields.Command.set([other_company.id])],
            }
        )
        membership = partner.create_cooperative_membership(self.env.company)
        membership.create_user()
        new_user = self.env["res.users"].search([("login", "=", "jane@example.com")])
        self.assertEqual(new_user, user)
        self.assertEqual(user.company_id, other_company)
        self.assertEqual(user.company_ids, self.env.company | other_company)

    def test_create_user_different_login(self):
        """If a partner has a user but the user has a different login address,
        correctly detect that.
        """
        partner = self.env["res.partner"].create(
            {"name": "Jane Doe", "email": "jane@example.com"}
        )
        other_company = self.env["res.company"].create({"name": "Foo Company"})
        user = self.env["res.users"].create(
            {
                "partner_id": partner.id,
                "login": "other@example.com",
                "company_id": other_company.id,
                "company_ids": [fields.Command.set([other_company.id])],
            }
        )
        membership = partner.create_cooperative_membership(self.env.company)
        membership.create_user()
        self.assertEqual(partner.user_ids, user)
        self.assertEqual(user.company_ids, self.env.company | other_company)
        self.assertFalse(
            self.env["res.users"].search([("login", "=", "jane@example.com")])
        )

    def test_create_user_multiple_users(self):
        """If a partner has multiple users, add the company to all of them."""
        partner = self.env["res.partner"].create(
            {"name": "Jane Doe", "email": "jane@example.com"}
        )
        other_company = self.env["res.company"].create({"name": "Foo Company"})
        active_user = self.env["res.users"].create(
            {
                "partner_id": partner.id,
                "login": "other@example.com",
                "company_id": other_company.id,
                "company_ids": [fields.Command.set([other_company.id])],
            }
        )
        inactive_user = self.env["res.users"].create(
            {
                "partner_id": partner.id,
                "login": "foobar@example.com",
                "company_id": other_company.id,
                "company_ids": [fields.Command.set([other_company.id])],
            }
        )
        inactive_user.active = False
        membership = partner.create_cooperative_membership(self.env.company)
        membership.create_user()
        self.assertEqual(len(partner.user_ids), 2)
        self.assertEqual(active_user.company_ids, self.env.company | other_company)
        self.assertEqual(inactive_user.company_ids, self.env.company)
        self.assertEqual(inactive_user.company_id, self.env.company)
        self.assertTrue(inactive_user.active)
