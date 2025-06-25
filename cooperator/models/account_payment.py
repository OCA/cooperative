# SPDX-FileCopyrightText: 2025 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import api, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    @api.depends(
        "journal_id",
        "partner_id",
        "partner_type",
        "is_internal_transfer",
        "destination_journal_id",
        "payment_transaction_id.invoice_ids.subscription_request",
    )
    def _compute_destination_account_id(self):
        # this is needed to ensure that payments created in the portal use the
        # correct destination account. otherwise they use a default account.
        # with this, the lines can be correctly reconciled and the capital
        # release request set as paid.
        for pay in self:
            if (
                pay.partner_type == "customer"
                and pay.payment_transaction_id.invoice_ids.subscription_request
            ):
                pay.destination_account_id = pay.company_id.property_cooperator_account
            else:
                super(AccountPayment, pay)._compute_destination_account_id()
        # this is just to silence W8110
        return None
