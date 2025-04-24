# SPDX-FileCopyrightText: 2022 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def write(self, vals):
        # For an explanation, see res_partner of cooperator_portal.
        if "national_number" in vals:
            del vals["national_number"]
        return super().write(vals)
