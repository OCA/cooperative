from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    share_payment_mode_id = fields.Many2one(
        comodel_name="account.payment.mode",
        company_dependent=True,
        check_company=True,
        domain="[('payment_type', '=', 'inbound')]",
    )
