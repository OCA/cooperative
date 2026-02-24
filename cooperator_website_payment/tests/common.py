# SPDX-FileCopyrightText: 2025 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import re

from odoo.tools import mute_logger

from odoo.addons.account_payment.tests.common import AccountPaymentCommon
from odoo.addons.cooperator.tests.cooperator_test_mixin import CooperatorTestMixin
from odoo.addons.payment.tests.http_common import PaymentHttpCommon


class CooperatorWebsitePaymentCommon(
    AccountPaymentCommon, PaymentHttpCommon, CooperatorTestMixin
):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_up_cooperator_test_data()
        # associate website with test company
        cls.env.ref("website.default_website").company_id = cls.env.company

    def _submit_subscription_form(self):
        # open subscription form
        result = self.url_open("/page/become_cooperator")
        csrf_token = re.search(
            r'<input type="hidden" name="csrf_token" value="(\w+?)"/>', result.text
        ).group(1)
        # submit subscription form
        form_data = {"csrf_token": csrf_token}
        dummy_subscription_requests_vals = self.get_dummy_subscription_requests_vals()
        for field in (
            "email",
            "firstname",
            "lastname",
            "birthdate",
            "address",
            "ordered_parts",
            "zip_code",
            "city",
            "iban",
            "gender",
            "country_id",
            "phone",
            "lang",
        ):
            form_data[field] = dummy_subscription_requests_vals[field]
        # the form except a product.template id, not a product.product
        form_data["share_product_id"] = self.share_y.product_tmpl_id.id
        form_data["confirm_email"] = form_data["email"]
        # FIXME: this should not be part of the form data, but computed by the
        # form controller.
        form_data["total_parts"] = self.share_y.list_price * form_data["ordered_parts"]
        url = self._build_url("/subscription/subscribe_share")
        return self.url_open(url, data=form_data)

    def _get_transaction_route_params_from_payment_page(self, text):
        csrf_token = re.search(r'csrf_token: "(\w+?)"', text).group(1)
        match = re.search(
            r'<form name="o_payment_checkout" class=".*?" '
            r'data-amount="(?P<amount>.+?)" '
            r'data-currency-id="(?P<currency_id>.+?)" '
            r'data-partner-id="(?P<partner_id>.+?)" '
            r'data-access-token="(?P<access_token>.+?)" '
            r'data-transaction-route="(?P<transaction_route>.+?)" '
            r'data-landing-route="(?P<landing_route>.+?)" '
            r'data-allow-token-selection="(?P<allow_token_selection>.+?)">',
            text,
        )
        return match.group("transaction_route"), {
            "payment_option_id": None,
            "reference_prefix": None,
            "amount": float(match.group("amount")),
            "currency_id": int(match.group("currency_id")),
            "partner_id": int(match.group("partner_id")),
            "flow": "direct",
            "tokenization_requested": False,
            "landing_route": match.group("landing_route"),
            "access_token": match.group("access_token"),
            "csrf_token": csrf_token,
            # this field is added by the account_payment module. it is not a
            # problem that it is not set, as the transaction route already
            # contains the invoice id.
            "invoice_id": None,
        }

    def _get_invoice_id_from_invoice_transaction_route(self, route):
        return int(re.match(r"/invoice/transaction/(\d+)", route).group(1))

    def _get_last_mail_id(self):
        return self.env["mail.mail"].search([], order="id desc", limit=1).id

    def _get_new_mail_messages(self, last_mail_id):
        return self.env["mail.mail"].search([("id", ">", last_mail_id)])

    def _create_payment_transaction(self, payment_page_result):
        route, params = self._get_transaction_route_params_from_payment_page(
            payment_page_result.text
        )
        capital_release_request_id = (
            self._get_invoice_id_from_invoice_transaction_route(route)
        )
        capital_release_request = (
            self.env["account.move"].sudo().browse(capital_release_request_id)
        )
        landing_route = params["landing_route"]
        params["payment_option_id"] = self.provider.id
        url = self._build_url(route)
        with mute_logger("odoo.addons.payment.models.payment_transaction"):
            result = self._make_json_rpc_request(url, params)
        processing_values = result.json()["result"]
        tx_sudo = self._get_tx(processing_values["reference"])
        return capital_release_request, landing_route, tx_sudo

    def _submit_form_and_create_transaction(self):
        result = self._submit_subscription_form()
        return self._create_payment_transaction(result)
