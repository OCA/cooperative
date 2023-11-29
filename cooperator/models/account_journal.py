# SPDX-FileCopyrightText: 2019 Coop IT Easy SC
# SPDX-FileContributor: Houssine Bakkali <houssine@coopiteasy.be>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    get_cooperator_payment = fields.Boolean("Get cooperator payments?")
    get_general_payment = fields.Boolean(string="Get general payments?")
