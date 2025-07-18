# SPDX-FileCopyrightText: 2025 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import fields, models


def get_company_type_selection():
    return [
        ("ag", "AG"),
        ("eg", "eG"),
        ("gmbh", "GmbH"),
        ("sdpr", "Stiftung des privaten Rechts"),
    ]


class ResPartner(models.Model):
    _inherit = "res.partner"

    legal_form = fields.Selection(selection_add=get_company_type_selection())
