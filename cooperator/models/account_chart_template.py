# Copyright 2023 Coop IT Easy SC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountChartTemplate(models.Model):
    _inherit = "account.chart.template"

    def generate_journals(self, acc_template_ref, company, journals_dict=None):
        super().generate_journals(acc_template_ref, company, journals_dict)
        self.env["subscription.request"].create_journal(company)
