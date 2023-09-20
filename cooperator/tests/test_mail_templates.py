# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from freezegun import freeze_time

from odoo.tests.common import TransactionCase

from .cooperator_test_mixin import CooperatorTestMixin


class TestMailTemplates(TransactionCase, CooperatorTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_up_cooperator_test_data()
        cls.default_template = cls.env.ref("cooperator.email_template_confirmation")

    def test_new_company_gets_default_template(self):
        """
        When creating a company, the mail template defaults to the default one.
        """
        company = self.env["res.company"].create({"name": "Test Company"})
        self.assertEqual(
            company.get_cooperator_confirmation_mail_template(), self.default_template
        )

    def test_overwrite_template(self):
        """By setting the field, the get function no longer returns the default
        mail template.
        """
        company = self.env["res.company"].create({"name": "Test Company"})
        template = self.env["mail.template"].create({"name": "Test"})
        company.cooperator_confirmation_mail_template = template
        self.assertEqual(company.get_cooperator_confirmation_mail_template(), template)

    def _get_last_mail_id(self):
        return self.env["mail.mail"].search([], order="id desc", limit=1).id

    def _get_new_mail_messages(self, last_mail_id):
        return self.env["mail.mail"].search([("id", ">", last_mail_id)])

    def test_mail_template_confirmation(self):
        """
        Test that creating a subscription request sends a confirmation message.
        """
        last_mail_id = self._get_last_mail_id()
        self.create_dummy_subscription_request()
        message = self._get_new_mail_messages(last_mail_id)
        self.assertEqual(len(message), 1)
        self.assertEqual(message.email_to, "email@example.net")
        self.assertIn("Hello first name,", message.body_html)
        self.assertNotIn("on behalf of", message.body_html)
        self.assertFalse(message.attachment_ids)

    def test_mail_template_confirmation_company(self):
        """
        Test that creating a subscription request for a company sends a
        confirmation message with correct values.
        """
        last_mail_id = self._get_last_mail_id()
        self.create_dummy_company_subscription_request()
        message = self._get_new_mail_messages(last_mail_id)
        self.assertEqual(len(message), 1)
        self.assertEqual(
            message.email_to, "email@example.net, companyemail@example.net"
        )
        self.assertIn("Hello first name,", message.body_html)
        self.assertIn("on behalf of dummy company", message.body_html)
        self.assertFalse(message.attachment_ids)

    def _test_mail_template_capital_release_request(self, subscription_request):
        last_mail_id = self._get_last_mail_id()
        subscription_request.validate_subscription_request()
        message = self._get_new_mail_messages(last_mail_id)
        self.assertEqual(len(message), 1)
        self.assertEqual(message.recipient_ids, subscription_request.partner_id)
        self.assertEqual(
            message.subject, "YourCompany Capital Release Request (Ref SUBJ/2023/001)"
        )
        self.assertIn("Hello first name,", message.body_html)
        self.assertEqual(len(message.attachment_ids), 1)
        # should be .pdf but pdf generation is disabled in test mode.
        self.assertEqual(message.attachment_ids.name, "SUBJ_2023_001.html")

    @freeze_time("2023-06-21")
    def test_mail_template_capital_release_request(self):
        """
        Test that validating a subscription request sends a message with the
        capital release request in attachment.
        """
        self._test_mail_template_capital_release_request(
            self.create_dummy_subscription_request()
        )

    @freeze_time("2023-06-21")
    def test_mail_template_capital_release_request_company(self):
        """
        Test that validating a subscription request for a company sends a
        message with the capital release request in attachment.
        """
        self._test_mail_template_capital_release_request(
            self.create_dummy_company_subscription_request()
        )

    def _test_mail_template_waiting_list(self, subscription_request):
        last_mail_id = self._get_last_mail_id()
        subscription_request.put_on_waiting_list()
        message = self._get_new_mail_messages(last_mail_id)
        self.assertEqual(len(message), 1)
        self.assertEqual(message.email_to, "email@example.net")
        self.assertIn("Hello first name,", message.body_html)
        self.assertFalse(message.attachment_ids)

    def test_mail_template_waiting_list(self):
        """
        Test that putting a subscription request on the waiting list sends a
        message with the correct values.
        """
        self._test_mail_template_waiting_list(self.create_dummy_subscription_request())

    def test_mail_template_waiting_list_company(self):
        """
        Test that putting a subscription request for a company on the waiting
        list sends a message with the correct values.
        """
        # shouldn't it be sent to the company email in this case?
        self._test_mail_template_waiting_list(
            self.create_dummy_company_subscription_request()
        )

    def _test_mail_template_certificate(self, subscription_request):
        subscription_request.validate_subscription_request()
        last_mail_id = self._get_last_mail_id()
        self.pay_invoice(subscription_request.capital_release_request)
        message = self._get_new_mail_messages(last_mail_id)
        self.assertEqual(len(message), 1)
        self.assertEqual(message.recipient_ids, subscription_request.partner_id)
        self.assertIn("Hello first name,", message.body_html)
        self.assertEqual(len(message.attachment_ids), 1)
        # should be .pdf but pdf generation is disabled in test mode.
        self.assertEqual(
            message.attachment_ids.name,
            "Certificate {number}.html".format(
                number=subscription_request.partner_id.cooperator_register_number
            ),
        )

    def test_mail_template_certificate(self):
        """
        Test that registering a payment for a capital release request sends a
        message with the cooperator certificate in attachment.
        """
        self._test_mail_template_certificate(self.create_dummy_subscription_request())

    def test_mail_template_certificate_company(self):
        """
        Test that registering a payment for a capital release request for a
        company sends a message with the cooperator certificate in attachment.
        """
        # the partner to which the message is sent is the company in this case.
        self._test_mail_template_certificate(
            self.create_dummy_company_subscription_request()
        )

    def _test_mail_template_share_increase(self, cooperator):
        subscription_request = self.create_dummy_subscription_from_partner(cooperator)
        subscription_request.validate_subscription_request()
        last_mail_id = self._get_last_mail_id()
        self.pay_invoice(subscription_request.capital_release_request)
        message = self._get_new_mail_messages(last_mail_id)
        self.assertEqual(len(message), 1)
        self.assertEqual(message.recipient_ids, subscription_request.partner_id)
        self.assertIn("Hello first name,", message.body_html)
        self.assertIn("for the new share(s) you have taken", message.body_html)
        self.assertEqual(len(message.attachment_ids), 1)
        # should be .pdf but pdf generation is disabled in test mode.
        self.assertEqual(
            message.attachment_ids.name,
            "Certificate {number}.html".format(
                number=cooperator.cooperator_register_number
            ),
        )

    def test_mail_template_share_increase(self):
        """
        Test that registering a payment for a capital release request for a
        share increase sends a message with the cooperator certificate in
        attachment.
        """
        self._test_mail_template_share_increase(self.create_dummy_cooperator())

    def test_mail_template_share_increase_company(self):
        """
        Test that registering a payment for a capital release request for a
        share increase for a company sends a message with the cooperator
        certificate in attachment.
        """
        self._test_mail_template_share_increase(self.create_dummy_company_cooperator())

    def _test_mail_template_share_transfer(self, cooperator):
        subscription_request = self.create_dummy_subscription_from_partner(cooperator)
        subscription_request.validate_subscription_request()
        last_mail_id = self._get_last_mail_id()
        self.pay_invoice(subscription_request.capital_release_request)
        message = self._get_new_mail_messages(last_mail_id)
        self.assertEqual(len(message), 1)
        self.assertEqual(message.recipient_ids, subscription_request.partner_id)
        self.assertIn("Hello first name,", message.body_html)
        self.assertIn("for the new share(s) you have taken", message.body_html)
        self.assertEqual(len(message.attachment_ids), 1)
        # should be .pdf but pdf generation is disabled in test mode.
        self.assertEqual(
            message.attachment_ids.name,
            "Certificate {number}.html".format(
                number=cooperator.cooperator_register_number
            ),
        )

    def test_mail_template_share_transfer(self):
        """
        Test that registering a payment for a capital release request for a
        share transfer sends a message with the cooperator certificate in
        attachment.
        """
        self._test_mail_template_share_transfer(self.create_dummy_cooperator())

    def test_mail_template_share_transfer_company(self):
        """
        Test that registering a payment for a capital release request for a
        share transfer for a company sends a message with the cooperator
        certificate in attachment.
        """
        self._test_mail_template_share_transfer(self.create_dummy_company_cooperator())
