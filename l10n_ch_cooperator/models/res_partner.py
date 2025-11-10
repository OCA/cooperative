# SPDX-FileCopyrightText: 2019 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import fields, models


def get_company_type_selection():
    return [
        ("ei", "Individual company"),
        ("snc", "Partnership"),
        ("sa", "Limited company (SA)"),
        ("sarl", "Limited liability company (Ltd)"),
        ("sc", "Cooperative"),
        ("asso", "Association"),
        ("fond", "Foundation"),
        ("edp", "Company under public law"),
    ]


class ResPartner(models.Model):
    _inherit = "res.partner"

    legal_form = fields.Selection(selection_add=get_company_type_selection())
