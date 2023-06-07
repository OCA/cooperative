# Copyright 2023 Coop IT Easy SC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountChartTemplate(models.Model):
    _inherit = "account.chart.template"

    def _load(self, sale_tax_rate, purchase_tax_rate, company):
        super()._load(sale_tax_rate, purchase_tax_rate, company)
        company._init_cooperator_data()
