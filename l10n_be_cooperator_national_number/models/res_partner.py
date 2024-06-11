# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import api, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def get_be_national_register_number_id_category(self):
        return self.env.ref(
            "l10n_be_partner_identification.l10n_be_national_registry_number_category"
        )

    def get_be_national_register_number_id_number(self):
        self.ensure_one()
        belgian_cat = self.get_be_national_register_number_id_category()
        return self.env["res.partner.id_number"].search(
            [
                ("partner_id", "=", self.id),
                ("category_id", "=", belgian_cat.id),
            ],
            limit=1,
        )

    def get_be_national_register_number(self):
        self.ensure_one()
        id_number = self.get_be_national_register_number_id_number()
        if id_number:
            return id_number.name
        return None

    def update_belgian_national_number(self, national_number):
        self.ensure_one()
        result = None
        if national_number:
            existing = self.get_be_national_register_number_id_number()
            # Update
            if existing:
                existing.name = national_number
                result = existing
            # Create new
            else:
                values = {
                    "name": national_number,
                    "category_id": self.get_be_national_register_number_id_category().id,
                    "partner_id": self.id,
                }
                result = self.env["res.partner.id_number"].create(values)
        return result
