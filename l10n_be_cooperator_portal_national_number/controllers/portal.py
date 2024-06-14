# SPDX-FileCopyrightText: 2024 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later


from odoo import _
from odoo.http import request, route

from odoo.addons.account.controllers.portal import PortalAccount


class CooperatorPortal(PortalAccount):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # See cooportal_portal/controllers/portal.py for why this code is the
        # way it is.
        if "OPTIONAL_BILLING_FIELDS" not in vars(self):
            self.OPTIONAL_BILLING_FIELDS = PortalAccount.OPTIONAL_BILLING_FIELDS.copy()
        self.OPTIONAL_BILLING_FIELDS.extend(["national_number"])

    def _prepare_portal_layout_values(self):
        values = super()._prepare_portal_layout_values()
        values[
            "display_national_number"
        ] = request.env.company.get_display_national_number(
            request.env.user.partner_id.is_company
        )
        national_number = request.env.user.partner_id.get_be_national_register_number()
        values["national_number"] = national_number
        return values

    def details_form_validate(self, data):
        error, error_message = super().details_form_validate(data)
        national_number = data.get("national_number")
        if national_number:
            valid = request.env["res.partner"].validate_be_national_register_number(
                national_number
            )
            if not valid:
                error["national_number"] = "error"
                error_message.append(_("The national number is not valid."))
        # Normally this should be in MANDATORY_BILLING_FIELDS, but national
        # number is conditionally required, which is tricky.
        if not national_number and request.env.company.get_require_national_number(
            request.env.user.partner_id.is_company
        ):
            error["national_number"] = "error"
            error_message.append(_("The national number is required."))
        return error, error_message

    @route(["/my/account"], type="http", auth="user", website=True)
    def account(self, redirect=None, **post):
        res = super().account(redirect, **post)
        if not res.qcontext.get("error"):
            national_number = post.get("national_number")
            request.env.user.partner_id.sudo().update_be_national_register_number(
                national_number
            )
        return res
