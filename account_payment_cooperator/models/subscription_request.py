from odoo import api, fields, models


class SubscriptionRequest(models.Model):
    _inherit = "subscription.request"

    payment_mode_id = fields.Many2one(
        comodel_name="account.payment.mode",
        compute="_compute_payment_mode",
        store=True,
        readonly=False,  # must be set False to compute
        states={
            "block": [("readonly", True)],
            "done": [("readonly", True)],
            "waiting": [("readonly", True)],
            "transfer": [("readonly", True)],
            "cancelled": [("readonly", True)],
            "paid": [("readonly", True)],
        },
        check_company=True,
        domain="[('payment_type', '=', 'inbound')]",
    )

    @api.depends("share_product_id")
    def _compute_payment_mode(self):
        for request in self:
            if request.share_product_id:
                request.payment_mode_id = request.share_product_id.share_payment_mode_id
            else:
                request.payment_mode_id = False

    def get_invoice_vals(self, partner):
        vals = super(SubscriptionRequest, self).get_invoice_vals(partner)
        if self.payment_mode_id:
            vals["payment_mode_id"] = self.payment_mode_id.id
            if (
                self.payment_mode_id.bank_account_link == "fixed"
                and self.payment_mode_id.payment_method_id.code == "manual"
            ):
                vals[
                    "partner_bank_id"
                ] = self.payment_mode_id.fixed_journal_id.bank_account_id.id
        return vals
