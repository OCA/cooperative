# SPDX-FileCopyrightText: 2025 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later


import odoo.tests

from odoo.addons.cooperator_website_payment.tests.common import (
    CooperatorWebsitePaymentCommon,
)


@odoo.tests.tagged("-at_install", "post_install")
class TestCooperatorWebsitePaymentCase(CooperatorWebsitePaymentCommon):
    def _setup_company_bank_account(self):
        self.company_account_iban = "BE91 5230 0000 0176"
        self.company_bank_account = self.env["res.partner.bank"].create(
            {
                "acc_number": self.company_account_iban,
                "partner_id": self.env.company.partner_id.id,
            }
        )
        self.env["account.journal"].create(
            {
                "name": self.company_account_iban,
                "type": "bank",
                "company_id": self.env.company.id,
                "bank_account_id": self.company_bank_account.id,
            }
        )

    def test_wire_transfer_payment(self):
        self._setup_company_bank_account()
        self.provider = self._prepare_provider(provider_code="custom")
        self.assertEqual(self.provider.custom_mode, "wire_transfer")
        last_mail_id = self._get_last_mail_id()
        (
            capital_release_request,
            landing_route,
            tx_sudo,
        ) = self._submit_form_and_create_transaction()
        partner = capital_release_request.subscription_request.partner_id
        self.assertEqual(capital_release_request.transaction_ids, tx_sudo)
        self.assertEqual(tx_sudo.partner_id, partner)
        self.url_open("/payment/custom/process", data={"reference": tx_sudo.reference})
        self.assertEqual(capital_release_request.payment_state, "not_paid")
        self.assertFalse(partner.member)
        result = self.url_open("/subscription/payment/validate")
        self.assertRegex(result.text, "Wire Transfer")
        self.assertRegex(result.text, "Total:")
        self.assertRegex(
            result.text,
            r'<strong>\$ <span class="oe_currency_value">50\.00</span></strong>',
        )
        self.assertRegex(
            result.text,
            "<h1><span>Subscription</span> "
            f"<em>{capital_release_request.name}</em> </h1>",
        )
        self.assertRegex(
            result.text,
            "Please use the following transfer details</h3>"
            "<h4>Bank Account</h4><ul><li>BE91 5230 0000 0176</li></ul>",
        )
        self.assertRegex(
            result.text,
            "<b>Communication: </b>"
            f"<span>{capital_release_request.payment_reference}</span>",
        )
        # should send a mail message containing the capital release request
        message = self._get_new_mail_messages(last_mail_id)
        self.assertEqual(len(message), 1)
        self.assertEqual(message.recipient_ids, partner)
        self.assertEqual(
            message.subject,
            "{company} Capital Release Request (Ref {reference})".format(
                company=self.env.company.name,
                reference=capital_release_request.name,
            ),
        )
        self.assertIn("Hello first name,", message.body_html)
        self.assertEqual(len(message.attachment_ids), 1)
        # should be .pdf but pdf generation is disabled in test mode.
        self.assertEqual(
            message.attachment_ids.name,
            "{filename}.html".format(
                filename=capital_release_request.name.replace("/", "_")
            ),
        )
        self.assertNotRegex(message.attachment_ids.raw, b"Your Contact:")
