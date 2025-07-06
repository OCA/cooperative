# SPDX-FileCopyrightText: 2024 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def send_capital_release_request_mail(self):
        # this is an override to allow to send the capital release request
        # email message only when needed.
        if not self.env.context.get("cooperator_website_payment_block_email"):
            return super().send_capital_release_request_mail()
