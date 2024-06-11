# SPDX-FileCopyrightText: 2016 Jairo Llopis <jairo.llopis@tecnativa.com>
# SPDX-FileCopyrightText: 2018 Coop IT Easy SC
# SPDX-FileContributor: Rémy Taymans <remy@coopiteasy.be>
# SPDX-FileContributor: Houssine Bakkali <houssine@coopiteasy.be>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import _
from odoo.http import request, route
from odoo.osv import expression

from odoo.addons.account.controllers.portal import PortalAccount, portal_pager


class CooperatorPortal(PortalAccount):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Class scope is accessible throughout the server even on
        # odoo instances that do not install this module.

        # Therefore : bring back to instance scope if not already
        #  if "MANDATORY_BILLING_FIELDS" in vars(self):
        if "MANDATORY_BILLING_FIELDS" not in vars(self):
            self.MANDATORY_BILLING_FIELDS = (
                PortalAccount.MANDATORY_BILLING_FIELDS.copy()
            )

        self.MANDATORY_BILLING_FIELDS.extend(
            ["iban", "birthdate_date", "gender", "lang"]
        )

    def _prepare_portal_layout_values(self):
        values = super()._prepare_portal_layout_values()
        # We assume that commercial_partner_id always point to the
        # partner itself or to the linked partner. So there is no
        # need to check if the partner is a "contact" or not.
        partner = request.env.user.partner_id
        coop_partner = partner.commercial_partner_id
        coop_membership = coop_partner.cooperative_membership_id
        partner_model = request.env["res.partner"]
        coop_bank = (
            request.env["res.partner.bank"]
            .sudo()
            .search([("partner_id", "=", coop_partner.id)], limit=1)
        )
        iban = ""
        if partner.bank_ids:
            iban = partner.bank_ids[0].acc_number

        fields_desc = partner_model.sudo().fields_get(["gender"])

        values.update(
            {
                "coop_partner": coop_partner,
                "coop_membership": coop_membership,
                "coop_bank": coop_bank,
                "iban": iban,
                "genders": fields_desc["gender"]["selection"],
                "langs": request.env["res.lang"].search([]),
            }
        )
        return values

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "capital_release_request_count" in counters:
            capital_release_request_count = (
                request.env["account.move"].search_count(
                    self._get_capital_release_requests_domain()
                )
                if request.env["account.move"].check_access_rights(
                    "read", raise_exception=False
                )
                else 0
            )
            values["capital_release_request_count"] = capital_release_request_count
        return values

    def _invoice_get_page_view_values(self, invoice, access_token, **kwargs):
        if not invoice.release_capital_request:
            return super()._invoice_get_page_view_values(
                invoice, access_token, **kwargs
            )
        # page_name is needed for the breadcrumbs
        values = {
            "page_name": "capital_release_request",
            "invoice": invoice,
        }
        return self._get_page_view_values(
            invoice,
            access_token,
            values,
            "my_capital_release_requests_history",
            False,
            **kwargs
        )

    def _get_invoices_domain(self):
        # this is an override. by default, capital release requests are
        # excluded from invoices. this allows to avoid to override
        # _prepare_my_invoices_values() and the handling of invoices in
        # _prepare_home_portal_values(). by using the context,
        # _prepare_home_portal_values() can be reused as it is for capital
        # release requests.
        capital_release_request = request.context.get("capital_release_requests", False)
        return expression.AND(
            [
                super()._get_invoices_domain(),
                [("release_capital_request", "=", capital_release_request)],
            ]
        )

    def _get_capital_release_requests_domain(self):
        return expression.AND(
            [super()._get_invoices_domain(), [("release_capital_request", "=", True)]]
        )

    def details_form_validate(self, data):
        error, error_message = super().details_form_validate(data)
        sub_req_model = request.env["subscription.request"]
        iban = data.get("iban")
        valid = sub_req_model.check_iban(iban)

        if not valid:
            error["iban"] = "error"
            error_message.append(_("The IBAN account number is not valid."))
        return error, error_message

    @route(["/my/account"], type="http", auth="user", website=True)
    def account(self, redirect=None, **post):
        partner = request.env.user.partner_id

        res = super().account(redirect, **post)
        if not res.qcontext.get("error"):
            partner_bank = request.env["res.partner.bank"]
            iban = post.get("iban")
            if iban:
                if partner.bank_ids:
                    bank_account = partner.bank_ids[0]
                    bank_account.acc_number = iban
                else:
                    partner_bank.sudo().create(
                        {"partner_id": partner.id, "acc_number": iban}
                    )
        return res

    # this method is a copy of PortalAccount.portal_my_invoices() from the
    # account module in odoo 16, with a few changes. please update accordingly
    # when porting to newer versions.
    @route(
        [
            "/my/capital_release_requests",
            "/my/capital_release_requests/page/<int:page>",
        ],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_capital_release_requests(
        self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw
    ):
        """Render a page with the list of release capital request.
        A release capital request is an invoice with a flag that tell
        if it's a capital request or not.
        """
        request.update_context(capital_release_requests=True)
        values = self._prepare_my_invoices_values(
            page, date_begin, date_end, sortby, filterby
        )
        # remove filters (not needed for capital release requests)
        del values["searchbar_filters"]
        # change page name (needed for breadcrumbs)
        values["page_name"] = "capital_release_request"

        # pager
        pager = portal_pager(**values["pager"])

        # content according to pager and archive selected
        invoices = values["invoices"](pager["offset"])
        request.session["my_capital_release_requests_history"] = invoices.ids[:100]

        values.update(
            {
                "invoices": invoices,
                "pager": pager,
            }
        )
        return request.render(
            "cooperator_portal.portal_my_capital_release_requests", values
        )

    def _show_report(self, model, report_type, report_ref, download=False):
        # override in order to not retrieve release capital request as invoices
        if isinstance(model, type(request.env["account.move"])):
            if model.release_capital_request:
                report_ref = "cooperator.action_cooperator_invoices"
        return super()._show_report(model, report_type, report_ref, download)

    @route(
        ["/my/capital_release_requests/<int:invoice_id>"],
        type="http",
        auth="public",
        website=True,
    )
    def portal_my_capital_release_request_detail(
        self, invoice_id, access_token=None, report_type=None, download=False, **kw
    ):
        return self.portal_my_invoice_detail(
            invoice_id, access_token, report_type, download, **kw
        )

    @route(
        ["/my/cooperator_certificate/pdf"],
        type="http",
        auth="user",
        website=True,
    )
    def get_cooperator_certificate(self, **kw):
        """Render the cooperator certificate pdf of the current user"""
        # Same comment about commercial_partner_id as in
        # _prepare_portal_layout_values().
        partner = request.env.user.partner_id.commercial_partner_id

        return self._show_report(
            model=partner,
            report_type="pdf",
            report_ref="cooperator.action_cooperator_report_certificate",
            download=True,
        )
