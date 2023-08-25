# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import api, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # ensure no taxes are added to capital release requests
    def _get_computed_taxes(self):
        if self.move_id.release_capital_request:
            return False
        return super()._get_computed_taxes()

    # ensure payment terms lines use the account for subscription requests.
    @api.depends("display_type", "company_id")
    def _compute_account_id(self):
        result = super()._compute_account_id()
        term_lines = self.filtered(lambda line: line.display_type == "payment_term")
        for line in term_lines:
            subscription_request = line.move_id.subscription_request
            if subscription_request:
                line.account_id = subscription_request.get_accounting_account()
        return result
