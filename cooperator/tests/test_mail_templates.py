# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from freezegun import freeze_time

from odoo import fields
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

    def _test_mail_template_share_transfer(self, cooperator, subscription_request_vals):
        subscription_request_vals.update(
            {
                "firstname": "first name 2",
                "lastname": "last name 2",
                "email": "email2@example.net",
                "is_operation": True,
                "source": "operation",
            }
        )
        last_mail_id = self._get_last_mail_id()
        operation_request = self.env["operation.request"].create(
            {
                "operation_type": "transfer",
                "partner_id": cooperator.id,
                "share_product_id": self.share_y.id,
                "quantity": 1,
                # TODO: this field should be computed or shouldn't exist.
                "receiver_not_member": True,
                "subscription_request": [
                    fields.Command.create(subscription_request_vals)
                ],
            }
        )
        # this must not send a subscription request confirmation message
        self.assertEqual(self._get_last_mail_id(), last_mail_id)
        operation_request.submit_operation()
        operation_request.approve_operation()
        operation_request.execute_operation()
        messages = self._get_new_mail_messages(last_mail_id)
        # there should be 2 messages: one for the receiver and one for the
        # sender.
        self.assertEqual(len(messages), 2)
        message = messages[0]
        self.assertEqual(message.recipient_ids, cooperator)
        self.assertIn("Hello first name,", message.body_html)
        self.assertIn("adaptation on your shares portfolio", message.body_html)
        self.assertEqual(len(message.attachment_ids), 1)
        # should be .pdf but pdf generation is disabled in test mode.
        self.assertEqual(
            message.attachment_ids.name,
            "Certificate {number}.html".format(
                number=cooperator.cooperator_register_number
            ),
        )
        message = messages[1]
        if subscription_request_vals.get("is_company"):
            new_cooperator_email = subscription_request_vals["company_email"]
        else:
            new_cooperator_email = subscription_request_vals["email"]
        new_cooperator = self.env["res.partner"].search(
            [("email", "=", new_cooperator_email)]
        )
        self.assertEqual(message.recipient_ids, new_cooperator)
        self.assertIn("Hello first name 2,", message.body_html)
        self.assertIn("shares have been transferred to you", message.body_html)
        self.assertEqual(len(message.attachment_ids), 1)
        # should be .pdf but pdf generation is disabled in test mode.
        self.assertEqual(
            message.attachment_ids.name,
            "Certificate {number}.html".format(
                number=new_cooperator.cooperator_register_number
            ),
        )

    def test_mail_template_share_transfer(self):
        """
        Test that executing a share transfer operation sends a message with
        the cooperator certificate in attachment.
        """
        self._test_mail_template_share_transfer(
            self.create_dummy_cooperator(), self.get_dummy_subscription_requests_vals()
        )

    def test_mail_template_share_transfer_company(self):
        """
        Test that executing a share transfer operation to a company sends a
        message with the cooperator certificate in attachment.
        """
        subscription_request_vals = self.get_dummy_company_subscription_requests_vals()
        subscription_request_vals.update(
            {
                "company_name": "dummy company 2",
                "company_email": "companyemail2@example.net",
                "company_register_number": "dummy company register number 2",
            }
        )
        self._test_mail_template_share_transfer(
            self.create_dummy_company_cooperator(), subscription_request_vals
        )

    def _test_mail_template_share_transfer_all_shares(
        self, cooperator, subscription_request_vals
    ):
        subscription_request_vals.update(
            {
                "firstname": "first name 2",
                "lastname": "last name 2",
                "email": "email2@example.net",
                "is_operation": True,
                "source": "operation",
            }
        )
        last_mail_id = self._get_last_mail_id()
        operation_request = self.env["operation.request"].create(
            {
                "operation_type": "transfer",
                "partner_id": cooperator.id,
                "share_product_id": self.share_y.id,
                # 2 is all the quality that the partner has.
                "quantity": 2,
                # TODO: this field should be computed or shouldn't exist.
                "receiver_not_member": True,
                "subscription_request": [
                    fields.Command.create(subscription_request_vals)
                ],
            }
        )
        # this must not send a subscription request confirmation message
        self.assertEqual(self._get_last_mail_id(), last_mail_id)
        operation_request.submit_operation()
        operation_request.approve_operation()
        operation_request.execute_operation()
        messages = self._get_new_mail_messages(last_mail_id)
        # there should be 2 messages: one for the receiver and one for the
        # sender.
        self.assertEqual(len(messages), 2)
        message = messages[0]
        self.assertEqual(message.recipient_ids, cooperator)
        self.assertIn("Hello first name,", message.body_html)
        self.assertIn("adaptation on your shares portfolio", message.body_html)
        self.assertIn("You have no remaining shares", message.body_html)
        self.assertEqual(len(message.attachment_ids), 0)
        # Don't test the other message; already tested by different test.

    def test_mail_template_share_transfer_all_shares(self):
        """
        Test that executing a share transfer wherein all shares are
        transferred sends a message with no certificate in attachment.
        """
        self._test_mail_template_share_transfer_all_shares(
            self.create_dummy_cooperator(), self.get_dummy_subscription_requests_vals()
        )

    def test_mail_template_share_transfer_all_shares_company(self):
        """
        Test that executing a share transfer from a company wherein all shares
        are transferred sends a message with no certificate in attachment.
        """
        self._test_mail_template_share_transfer_all_shares(
            self.create_dummy_company_cooperator(),
            self.get_dummy_subscription_requests_vals(),
        )

    def _test_mail_template_share_transfer_existing_cooperator(
        self, cooperator, subscription_request_vals
    ):
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
        if subscription_request_vals.get("is_company"):
            new_cooperator_email = subscription_request_vals["company_email"]
        else:
            new_cooperator_email = subscription_request_vals["email"]
        new_cooperator = self.env["res.partner"].search(
            [("email", "=", new_cooperator_email)]
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
        last_mail_id = self._get_last_mail_id()
        operation_request.execute_operation()
        messages = self._get_new_mail_messages(last_mail_id)
        # there should be 2 messages: one for the receiver and one for the
        # sender.
        self.assertEqual(len(messages), 2)
        message = messages[0]
        self.assertEqual(message.recipient_ids, cooperator)
        self.assertIn("Hello first name,", message.body_html)
        self.assertIn("adaptation on your shares portfolio", message.body_html)
        self.assertEqual(len(message.attachment_ids), 1)
        # should be .pdf but pdf generation is disabled in test mode.
        self.assertEqual(
            message.attachment_ids.name,
            "Certificate {number}.html".format(
                number=cooperator.cooperator_register_number
            ),
        )
        message = messages[1]
        self.assertEqual(message.recipient_ids, new_cooperator)
        self.assertIn("Hello first name 2,", message.body_html)
        self.assertIn("shares have been transferred to you", message.body_html)
        self.assertEqual(len(message.attachment_ids), 1)
        # should be .pdf but pdf generation is disabled in test mode.
        self.assertEqual(
            message.attachment_ids.name,
            "Certificate {number}.html".format(
                number=new_cooperator.cooperator_register_number
            ),
        )

    def test_mail_template_share_transfer_existing_cooperator(self):
        """
        Test that executing a share transfer operation to an existing
        cooperator sends a message with the cooperator certificate in
        attachment.
        """
        self._test_mail_template_share_transfer_existing_cooperator(
            self.create_dummy_cooperator(), self.get_dummy_subscription_requests_vals()
        )

    def test_mail_template_share_transfer_existing_cooperator_company(self):
        """
        Test that executing a share transfer operation to an existing company
        cooperator sends a message with the cooperator certificate in
        attachment.
        """
        subscription_request_vals = self.get_dummy_company_subscription_requests_vals()
        subscription_request_vals.update(
            {
                "company_name": "dummy company 2",
                "company_email": "companyemail2@example.net",
                "company_register_number": "dummy company register number 2",
            }
        )
        self._test_mail_template_share_transfer_existing_cooperator(
            self.create_dummy_company_cooperator(), subscription_request_vals
        )
