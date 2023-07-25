# Copyright 2019 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date, datetime, timedelta

from freezegun import freeze_time

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.fields import Date
from odoo.tests.common import SavepointCase, users

from .cooperator_test_mixin import CooperatorTestMixin


class CooperatorCase(SavepointCase, CooperatorTestMixin):
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
    def test_register_payment_for_capital_release(self):
        self.validate_subscription_request_and_pay(self.subscription_request_1)
        invoice = self.subscription_request_1.capital_release_request
        self.assertEqual(invoice.state, "posted")

        partner = self.subscription_request_1.partner_id
        self.assertFalse(partner.coop_candidate)
        self.assertTrue(partner.member)
        self.assertTrue(partner.share_ids)
        self.assertEqual(partner.effective_date, Date.today())

        share = partner.share_ids[0]
        self.assertEqual(share.share_number, self.subscription_request_1.ordered_parts)
        self.assertEqual(
            share.share_product_id, self.subscription_request_1.share_product_id
        )
        self.assertEqual(share.effective_date, Date.today())

    @users("user-cooperator")
    def test_effective_date_from_payment_date(self):
        self.subscription_request_1.validate_subscription_request()
        invoice = self.subscription_request_1.capital_release_request
        self.pay_invoice(invoice, date(2022, 6, 21))

        partner = self.subscription_request_1.partner_id
        self.assertEqual(partner.effective_date, date(2022, 6, 21))

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
        partner2.create_cooperative_membership(self.company.id)
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
        company_partner2.create_cooperative_membership(self.company.id)
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
        subscription_request = (
            self.env["subscription.request"]
            .with_company(company_2)
            .create(self.get_dummy_subscription_requests_vals())
        )
        # validate subscription request for company_2 but with self.company as
        # the current company.
        subscription_request.with_company(self.company).validate_subscription_request()
        invoice = subscription_request.capital_release_request
        self.assertEqual(invoice.company_id, company_2)
        # register a payment for company_2 but with self.company as the
        # current company.
        self.pay_invoice(invoice.with_company(self.company))
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
