# SPDX-FileCopyrightText: 2024 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import http
from odoo.http import request
from odoo.tools import html_escape, html_sanitize

from odoo.addons.cooperator_website.controllers.main import WebsiteSubscription
from odoo.addons.payment.controllers.portal import PaymentPortal


class WebsiteSubscriptionPayment(WebsiteSubscription):
    PAYMENT_ROUTE = "/subscription/payment"
    VALIDATION_ROUTE = "/subscription/payment/validate"
    CONFIRMATION_ROUTE = "/subscription/confirmation"

    def get_subscription_response(self, values, kwargs):
        subscription_request = values["subscription_request"]
        capital_release_request = subscription_request.with_context(
            cooperator_website_payment_block_email=True
        ).validate_subscription_request()
        request.session["capital_release_request_id"] = capital_release_request.id
        return request.redirect(self.PAYMENT_ROUTE)

    def _get_capital_release_request(self):
        capital_release_request_id = request.session.get("capital_release_request_id")
        return request.env["account.move"].sudo().browse(capital_release_request_id)

    @http.route(PAYMENT_ROUTE, type="http", auth="public", website=True, sitemap=False)
    def subscription_payment(self, **post):
        capital_release_request = self._get_capital_release_request()
        if not capital_release_request:
            return request.redirect("/")
        if not capital_release_request._has_to_be_paid():
            return request.redirect(self.CONFIRMATION_ROUTE)
        render_values = self._get_payment_values(capital_release_request)
        return request.render("cooperator_website_payment.payment", render_values)

    def _get_payment_values(self, capital_release_request, **kwargs):
        # this is a copy of WebsiteSale._get_shop_payment_values() (from the
        # website_sale module) with some changes.
        currency = capital_release_request.currency_id
        user = request.env.user
        logged_in = not user._is_public()
        partner = user.partner_id
        amount = capital_release_request.amount_total
        # in sudo mode to read the fields of providers, capital_release_request
        # and partner (if not logged in)
        providers_sudo = (
            request.env["payment.provider"]
            .sudo()
            ._get_compatible_providers(
                capital_release_request.company_id.id,
                partner.id,
                amount,
                currency_id=currency.id,
                website_id=request.website.id,
            )
        )
        tokens = (
            request.env["payment.token"].search(
                [
                    ("provider_id", "in", providers_sudo.ids),
                    ("partner_id", "=", partner.id),
                ]
            )
            if logged_in
            else request.env["payment.token"]
        )
        fees_by_provider = {
            p_sudo: p_sudo._compute_fees(amount, currency, partner.country_id)
            for p_sudo in providers_sudo.filtered("fees_active")
        }
        return {
            "error": self._get_subscription_payment_error(capital_release_request),
            "partner": partner,
            "payment_action_id": request.env.ref("payment.action_payment_provider").id,
            # payment form common (checkout and manage) values
            "providers": providers_sudo,
            "tokens": tokens,
            "fees_by_provider": fees_by_provider,
            "show_tokenize_input": PaymentPortal._compute_show_tokenize_input_mapping(
                providers_sudo, logged_in=logged_in
            ),
            "amount": amount,
            "currency": currency,
            "partner_id": partner.id,
            "access_token": capital_release_request._portal_ensure_token(),
            "transaction_route": f"/invoice/transaction/{capital_release_request.id}",
            "landing_route": self.VALIDATION_ROUTE,
        }

    def _get_subscription_payment_error(self, capital_release_request):
        tx = capital_release_request.get_portal_last_transaction()
        if not tx or tx.state not in ("cancel", "error"):
            return None
        if tx.state == "error":
            return html_sanitize(f"<p>{html_escape(tx.state_message)}</p>")
        if tx.state == "cancel":
            return tx.provider_id.cancel_msg

    @http.route(
        VALIDATION_ROUTE,
        type="http",
        auth="public",
        website=True,
        sitemap=False,
    )
    def subscription_payment_validate(self, **kwargs):
        capital_release_request = self._get_capital_release_request()
        if not capital_release_request:
            return request.redirect("/")
        tx = capital_release_request.get_portal_last_transaction()
        if tx.state in ("pending", "authorized", "done"):
            return request.redirect(self.CONFIRMATION_ROUTE)
        return request.redirect(self.PAYMENT_ROUTE)

    @http.route(
        CONFIRMATION_ROUTE,
        type="http",
        auth="public",
        website=True,
        sitemap=False,
    )
    def subscription_confirmation(self, **kwargs):
        capital_release_request = self._get_capital_release_request()
        if not capital_release_request:
            return request.redirect("/")
        values = {
            "invoice": capital_release_request,
        }
        return request.render("cooperator_website_payment.confirmation", values)
