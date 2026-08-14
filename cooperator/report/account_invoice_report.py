from odoo import api, fields, models
from odoo.tools import SQL


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    release_capital_request = fields.Boolean(string="Release capital request")

    def _select(self) -> SQL:
        # since v18 _select() composes SQL objects, not strings
        return SQL(
            "%s, move.release_capital_request as release_capital_request",
            super()._select(),
        )

    @api.model
    def _where_calc(self, domain, active_test=True):
        # capital release requests should be excluded from reports. this is also used by
        # res.partner._invoice_total().
        domain = domain.copy()
        domain.append(("release_capital_request", "=", False))
        return super()._where_calc(domain, active_test)
