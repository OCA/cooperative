# SPDX-FileCopyrightText: 2025 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import odoo.tests
from odoo.tools import mute_logger

from odoo.addons.account_payment.tests.common import AccountPaymentCommon
from odoo.addons.payment.tests.http_common import PaymentHttpCommon

from .cooperator_test_mixin import CooperatorTestMixin

# while this test requires the account_payment module to be installed and
# cooperator does not depend on account_payment, in practice it works because
# account_payment gets installed automatically when account is installed. this
# test is here because it covers code present in this module.


@odoo.tests.tagged("-at_install", "post_install")
class PortalPaymentCase(AccountPaymentCommon, PaymentHttpCommon, CooperatorTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_up_cooperator_test_data()

    def test_portal_payment(self):
        self.subscription_request_1.validate_subscription_request()
        invoice = self.subscription_request_1.capital_release_request
        access_token = invoice._portal_ensure_token()
        route = f"/invoice/transaction/{invoice.id}"
        url = self._build_url(route)
        data = {
            "payment_option_id": self.provider.id,
            "amount": 75,
            "currency_id": invoice.currency_id.id,
            "flow": "direct",
            "tokenization_requested": False,
            "landing_route": (
                f"/my/capital_release_requests/{invoice.id}"
                f"?access_token={access_token}"
            ),
            "access_token": access_token,
        }
        with mute_logger("odoo.addons.payment.models.payment_transaction"):
            result = self._make_json_rpc_request(url, data)
        processing_values = result.json()["result"]
        tx_sudo = self._get_tx(processing_values["reference"])
        self.assertEqual(invoice.transaction_ids, tx_sudo)
        tx_sudo._set_done()
        tx_sudo._finalize_post_processing()
        self.assertEqual(invoice.payment_state, "paid")
        partner = self.subscription_request_1.partner_id
        self.assertTrue(partner.member)
