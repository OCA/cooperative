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
            "l10n_be_partner_identification.l10n_be_national_registry_number_category"
        ).id
        national_number = partner.id_numbers.filtered(
            lambda rec: rec.category_id.id == national_number_id_category
        )
        return national_number.name

    def validate_subscription_request(self):
        self.ensure_one()
        if self.require_national_number and not self.national_number:
            raise UserError(_("National Number is required."))
        invoice = super().validate_subscription_request()
        if not self.is_company:
            partner = invoice.partner_id
            partner.update_belgian_national_number(self.national_number)
        return invoice

    def get_person_info(self, partner):
        super().get_person_info(partner)
        self.national_number = self.get_national_number_from_partner(partner)
        return True
