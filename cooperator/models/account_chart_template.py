# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import models


class AccountChartTemplate(models.Model):
    _inherit = "account.chart.template"

    def _load(self, company):
        result = super()._load(company)
        company._init_cooperator_data()
        return result
