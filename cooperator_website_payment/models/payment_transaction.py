# SPDX-FileCopyrightText: 2025 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import models


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def _is_wire_transfer(self):
        self.ensure_one()
        return (
            self.provider_code == "custom"
            and self.provider_id.custom_mode == "wire_transfer"
        )

    def _ensure_bank_account_number_in_pending_message(self):
        accounts = (
            self.env["account.journal"]
            .sudo()
            .search(
                [
                    ("type", "=", "bank"),
                    ("company_id", "=", self.provider_id.company_id.id),
                ]
            )
            .bank_account_id
        )
        if not accounts:
            return
        if accounts[0].display_name not in self.provider_id.pending_msg:
            self.provider_id.pending_msg = None
            self.provider_id._transfer_ensure_pending_msg_is_set()

    def _process_notification_data(self, notification_data):
        if self._is_wire_transfer():
            for invoice in self.invoice_ids.filtered(
                lambda inv: inv.release_capital_request
            ):
                invoice.send_capital_release_request_mail()
            self._ensure_bank_account_number_in_pending_message()
        return super()._process_notification_data(notification_data)
