# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later


from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SubscriptionRequest(models.Model):
    _inherit = "subscription.request"

    national_number = fields.Char()
    display_national_number = fields.Boolean(
        compute="_compute_display_national_number",
    )
    require_national_number = fields.Boolean(
        compute="_compute_require_national_number",
    )

    @api.depends("is_company", "company_id", "company_id.display_national_number")
    def _compute_display_national_number(self):
        for request in self:
            request.display_national_number = (
                request.company_id.get_display_national_number(request.is_company)
            )

    @api.depends("is_company", "company_id", "company_id.require_national_number")
    def _compute_require_national_number(self):
        for request in self:
            request.require_national_number = (
                request.company_id.get_require_national_number(request.is_company)
            )

    def validate_subscription_request(self):
        self.ensure_one()
        if self.require_national_number and not self.national_number:
            raise UserError(_("National Number is required."))
        if self.national_number:
            self.env["res.partner"].validate_be_national_register_number(
                self.national_number, error=True
            )
        invoice = super().validate_subscription_request()
        if not self.is_company:
            partner = invoice.partner_id
            partner.update_be_national_register_number(self.national_number)
        return invoice

    def set_person_info(self, partner):
        super().set_person_info(partner)
        self.national_number = partner.get_be_national_register_number()
        return True
