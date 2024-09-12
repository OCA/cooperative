from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    display_national_number = fields.Boolean(
        related="company_id.display_national_number", readonly=False
    )
    require_national_number = fields.Boolean(
        related="company_id.require_national_number", readonly=False
    )
