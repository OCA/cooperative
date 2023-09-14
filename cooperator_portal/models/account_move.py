# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _compute_access_url(self):
        result = super()._compute_access_url()
        for move in self.filtered(lambda move: move.release_capital_request):
            move.access_url = "/my/capital_release_requests/{move_id}".format(
                move_id=move.id
            )
        return result
