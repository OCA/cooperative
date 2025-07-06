# SPDX-FileCopyrightText: 2025 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later


import odoo.tests

from .common import CooperatorWebsitePaymentCommon


@odoo.tests.tagged("-at_install", "post_install")
class CooperatorWebsitePaymentCase(CooperatorWebsitePaymentCommon):
    def test_show_payment_page(self):
        result = self._submit_subscription_form()
        # should redirect to payment page
        self.assertRegex(result.text, "<h2.*?>Please select a payment method</h2>")
        # should display the amount
        self.assertRegex(
            result.text,
            r"<p.*?>Subscription amount: "
            r'<strong data-oe-type="monetary" data-oe-expression="amount">'
            r'\$ <span class="oe_currency_value">50\.00</span></strong></p>',
        )

    def test_direct_payment(self):
        last_mail_id = self._get_last_mail_id()
        (
            capital_release_request,
            landing_route,
            tx_sudo,
        ) = self._submit_form_and_create_transaction()
        # should create a capital release request
        self.assertTrue(capital_release_request)
        partner = capital_release_request.subscription_request.partner_id
        self.assertFalse(partner.member)
        self.assertEqual(landing_route, "/subscription/payment/validate")
        self.assertEqual(capital_release_request.transaction_ids, tx_sudo)
        self.assertEqual(tx_sudo.partner_id, partner)
        self.assertEqual(capital_release_request.partner_id, partner)
        tx_sudo._set_done()
        tx_sudo._finalize_post_processing()
        self.assertEqual(capital_release_request.payment_state, "paid")
        self.assertTrue(partner.member)
        payment = tx_sudo.payment_id
        self.assertTrue(payment)
        self.assertEqual(payment.amount, capital_release_request.amount_total)
        self.assertEqual(payment.reconciled_invoice_ids, capital_release_request)
        # should send a mail message containing the cooperator certificate
        message = self._get_new_mail_messages(last_mail_id)
        self.assertEqual(len(message), 1)
        self.assertEqual(message.recipient_ids, partner)
        self.assertEqual(message.subject, "Payment Received Confirmation")
        self.assertIn("Hello first name,", message.body_html)
        self.assertEqual(len(message.attachment_ids), 1)
        # should be .pdf but pdf generation is disabled in test mode.
        self.assertEqual(
            message.attachment_ids.name,
            "Certificate {number}.html".format(
                number=partner.cooperator_register_number
            ),
        )
        result = self.url_open(landing_route)
        self.assertRegex(
            result.text,
            "<h1><span>Subscription</span> "
            f"<em>{capital_release_request.name}</em> "
            "<span>Confirmed</span></h1>",
        )
        self.assertRegex(
            result.text,
            r"<h2>Thank you for your subscription\.</h2>\s*"
            "<p>A confirmation message with your cooperator certificate has "
            r"been sent to you by email \(to "
            r"<strong>email@example.net</strong>\)\.</p>",
        )
        self.assertRegex(
            result.text,
            r"<p>Your payment has been successfully processed\. Thank you!</p>",
        )

    def test_failed_direct_payment(self):
        last_mail_id = self._get_last_mail_id()
        (
            capital_release_request,
            landing_route,
            tx_sudo,
        ) = self._submit_form_and_create_transaction()
        partner = capital_release_request.subscription_request.partner_id
        tx_sudo._set_error("dummy error")
        # it is not paid, because tx_sudo._finalize_post_processing() is only
        # called when the transaction is done. unfortunately, this cannot be
        # tested here.
        self.assertEqual(capital_release_request.payment_state, "not_paid")
        self.assertFalse(partner.member)
        result = self.url_open(landing_route)
        # should redirect to payment page with an error message
        self.assertRegex(
            result.text,
            r'<div class="alert alert-danger">\s*'
            r"<strong>The payment operation has failed:</strong>\s*"
            r"<p>dummy error</p>\s*Please try again.\s*</div>",
        )
        self.assertRegex(result.text, "<h2.*?>Please select a payment method</h2>")
        self.assertRegex(
            result.text,
            r"<p.*?>Subscription amount: "
            r'<strong data-oe-type="monetary" data-oe-expression="amount">'
            r'\$ <span class="oe_currency_value">50\.00</span></strong></p>',
        )
        # should not send a mail message
        message = self._get_new_mail_messages(last_mail_id)
        self.assertEqual(len(message), 0)

    def test_canceled_direct_payment(self):
        last_mail_id = self._get_last_mail_id()
        (
            capital_release_request,
            landing_route,
            tx_sudo,
        ) = self._submit_form_and_create_transaction()
        partner = capital_release_request.subscription_request.partner_id
        tx_sudo._set_canceled()
        # it is not paid, because tx_sudo._finalize_post_processing() is only
        # called when the transaction is done. unfortunately, this cannot be
        # tested here.
        self.assertEqual(capital_release_request.payment_state, "not_paid")
        self.assertFalse(partner.member)
        result = self.url_open(landing_route)
        # should redirect to payment page with an error message
        self.assertRegex(
            result.text,
            r'<div class="alert alert-danger">\s*'
            r"<strong>The payment operation has failed:</strong>\s*"
            r"<p>Your payment has been cancelled.</p>\s*Please try again.\s*</div>",
        )
        self.assertRegex(result.text, "<h2.*?>Please select a payment method</h2>")
        self.assertRegex(
            result.text,
            r"<p.*?>Subscription amount: "
            r'<strong data-oe-type="monetary" data-oe-expression="amount">'
            r'\$ <span class="oe_currency_value">50\.00</span></strong></p>',
        )
        # should not send a mail message
        message = self._get_new_mail_messages(last_mail_id)
        self.assertEqual(len(message), 0)

    def test_retry_failed_direct_payment(self):
        last_mail_id = self._get_last_mail_id()
        (
            capital_release_request,
            landing_route,
            tx_sudo,
        ) = self._submit_form_and_create_transaction()
        partner = capital_release_request.subscription_request.partner_id
        tx_sudo._set_error("dummy error")
        result = self.url_open(landing_route)
        # should redirect to payment page with an error message
        self.assertRegex(result.text, "<h2.*?>Please select a payment method</h2>")
        (
            capital_release_request_2,
            landing_route,
            tx_sudo_2,
        ) = self._create_payment_transaction(result)
        # should use the same capital release request
        self.assertEqual(capital_release_request_2, capital_release_request)
        # should create a new transaction
        self.assertNotEqual(tx_sudo_2, tx_sudo)
        tx_sudo._set_done()
        tx_sudo._finalize_post_processing()
        self.assertEqual(capital_release_request.payment_state, "paid")
        self.assertTrue(partner.member)
        result = self.url_open(landing_route)
        self.assertRegex(
            result.text,
            "<h1><span>Subscription</span> "
            f"<em>{capital_release_request.name}</em> "
            "<span>Confirmed</span></h1>",
        )
        # should send a mail message containing the cooperator certificate
        message = self._get_new_mail_messages(last_mail_id)
        self.assertEqual(len(message), 1)
        self.assertEqual(message.recipient_ids, partner)
        self.assertEqual(message.subject, "Payment Received Confirmation")
        self.assertIn("Hello first name,", message.body_html)
        self.assertEqual(len(message.attachment_ids), 1)
        # should be .pdf but pdf generation is disabled in test mode.
        self.assertEqual(
            message.attachment_ids.name,
            "Certificate {number}.html".format(
                number=partner.cooperator_register_number
            ),
        )

    def test_reload_payment_page_after_successful_direct_payment(self):
        (
            capital_release_request,
            landing_route,
            tx_sudo,
        ) = self._submit_form_and_create_transaction()
        partner = capital_release_request.subscription_request.partner_id
        tx_sudo._set_done()
        tx_sudo._finalize_post_processing()
        self.assertEqual(capital_release_request.payment_state, "paid")
        self.assertTrue(partner.member)
        # go back to payment page
        result = self.url_open("/subscription/payment")
        # should redirect to the confirmation page
        self.assertRegex(
            result.text,
            "<h1><span>Subscription</span> "
            f"<em>{capital_release_request.name}</em> "
            "<span>Confirmed</span></h1>",
        )

    def test_test_module_installed(self):
        # this is to ensure that the companion test module is kept together
        # with this module in future versions.
        test_module = self.env["ir.module.module"].search(
            [("name", "=", "test_cooperator_website_payment")]
        )
        self.assertTrue(
            test_module,
            msg="test_cooperator_website_payment module must exist",
        )
        self.assertEqual(
            test_module.state,
            "installed",
            msg="test_cooperator_website_payment module must be installed",
        )
