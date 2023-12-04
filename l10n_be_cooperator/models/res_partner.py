# SPDX-FileCopyrightText: 2019 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import fields, models


def get_company_type_selection():
    # this list comes from
    # https://www.belgium.be/fr/economie/entreprise/creation/types_de_societe
    return [
        ("aisbl", "AISBL"),
        ("asbl", "ASBL"),
        ("sa", "SA"),
        ("sc", "SC"),
        ("scomm", "SComm"),
        ("snc", "SNC"),
        ("srl", "SRL"),
        # former types (before 2019)
        ("scrl", "SCRL"),
        ("sprl", "SPRL"),
    ]


class ResPartner(models.Model):
    _inherit = "res.partner"

    legal_form = fields.Selection(selection_add=get_company_type_selection())
