from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SubscriptionRequest(models.Model):
    _inherit = "subscription.request"

    national_number = fields.Char(string="National Number")
    display_national_number = fields.Boolean(
        compute="_compute_display_national_number",
    )
    require_national_number = fields.Boolean(
        compute="_compute_require_national_number",
    )

    @api.depends("is_company", "company_id", "company_id.display_national_number")
    def _compute_display_national_number(self):
        self.display_national_number = (
            self.company_id.display_national_number and not self.is_company
        )

    @api.depends("is_company", "company_id", "company_id.require_national_number")
    def _compute_require_national_number(self):
        self.require_national_number = (
            self.company_id.require_national_number and not self.is_company
        )

    def get_national_number_from_partner(self, partner):
        national_number_id_category = self.env.ref(
            "l10n_be_national_number.l10n_be_national_number_category"
        ).id
        national_number = partner.id_numbers.filtered(
            lambda rec: rec.category_id.id == national_number_id_category
        )
        return national_number.name

    def validate_subscription_request(self):
        self.ensure_one()
        if self.require_national_number and not self.national_number:
            raise UserError(_("National Number is required."))
        super().validate_subscription_request()

    def create_national_number(self, partner):
        if not self.is_company:
            values = {
                "name": self.national_number,
                "category_id": self.env.ref(
                    "l10n_be_national_number.l10n_be_national_number_category"  # noqa
                ).id,
                "partner_id": partner.id,
            }
            self.env["res.partner.id_number"].create(values)
        return partner

    def create_coop_partner(self):
        partner = super().create_coop_partner()
        if self.require_national_number:
            self.create_national_number(partner)
        return partner

    def get_representative_vals(self):
        contact_vals = super().get_representative_vals()
        contact_vals["national_number"] = self.national_number
        return contact_vals

    def get_partner_vals(self):
        contact_vals = super().get_partner_vals()
        contact_vals["national_number"] = self.national_number
        return contact_vals

    def get_person_info(self, partner):
        super().get_person_info(partner)
        self.national_number = self.get_national_number_from_partner(partner)

    def update_partner_info(self):
        self.create_national_number(self.partner_id)
        super().update_partner_info()
