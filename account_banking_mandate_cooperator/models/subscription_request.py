from odoo import _, fields, models
from odoo.exceptions import ValidationError


class SubscriptionRequest(models.Model):
    _inherit = "subscription.request"

    mandate_id = fields.Many2one(
        "account.banking.mandate",
        string="Direct Debit Mandate",
        ondelete="restrict",
        check_company=True,
        readonly=False,
        domain="[('state', 'in', ('draft', 'valid'))]",
    )
    mandate_required = fields.Boolean(
        related="payment_mode_id.payment_method_id.mandate_required",
    )
    mandate_approved = fields.Boolean(
        required=True, default=False, string="Approved creation of new mandate"
    )

    def get_invoice_vals(self, partner):
        vals = super(SubscriptionRequest, self).get_invoice_vals(partner)
        vals["mandate_id"] = self.mandate_id.id or False
        return vals

    def create_invoice(self, partner):
        if self.mandate_approved and not self.mandate_id:
            mandate_id = self.create_mandate()
            self.mandate_id = mandate_id
        return super(SubscriptionRequest, self).create_invoice(partner)

    def get_bank(self):
        if self.iban:
            bank_id = self.partner_id.bank_ids.search(
                [("acc_number", "ilike", self.iban)]
            )  # TODO normalize iban
            if bank_id:
                return bank_id
            return self.env["res.partner.bank"].create(
                {
                    "partner_id": self.partner_id.id,
                    "acc_number": self.iban,
                }
            )
        return False

    def create_mandate(self):
        if self.partner_id and self.mandate_approved:
            values = self.get_mandate_values()
            if not values["partner_bank_id"]:
                raise ValidationError(
                    _("There isn't a valid bank to create the mandate.")
                )
            return self.env["account.banking.mandate"].create(values)
        return False

    def get_mandate_values(self):
        bank_id = self.get_bank()
        return {
            "format": "basic",
            "type": "generic",
            "state": "valid",
            "signature_date": self.date,
            "partner_bank_id": bank_id.id,
            "partner_id": self.partner_id.id,
            "company_id": self.partner_id.company_id.id,
        }
