# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def update_belgian_national_number(self, national_number):
        self.ensure_one()
        result = None
        if national_number:
            belgian_cat = self.env.ref(
                "l10n_be_partner_identification.l10n_be_national_registry_number_category"
            )
            existing = self.env["res.partner.id_number"].search(
                [
                    ("partner_id", "=", self.id),
                    ("category_id", "=", belgian_cat.id),
                ]
            )
            # Update
            if existing:
                existing.name = national_number
                result = existing
            # Create new
            else:
                values = {
                    "name": national_number,
                    "category_id": belgian_cat.id,
                    "partner_id": self.id,
                }
                result = self.env["res.partner.id_number"].create(values)
        return result
