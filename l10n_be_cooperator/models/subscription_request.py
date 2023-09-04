# SPDX-FileCopyrightText: 2019 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import fields, models

from . import res_partner


class SubscriptionRequest(models.Model):
    _inherit = "subscription.request"

    company_type = fields.Selection(
        selection_add=res_partner.get_company_type_selection()
    )
