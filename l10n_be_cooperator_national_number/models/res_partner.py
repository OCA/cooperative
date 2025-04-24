# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from collections import namedtuple

from odoo import api, models
from odoo.exceptions import ValidationError


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

    @api.model
    def validate_be_national_register_number(self, national_number, error=False):
        """Verify whether the national number is valid. Returns True if valid.

        If error is True, a ValidationError is raised instead.
        """
        belgian_cat = self.sudo().get_be_national_register_number_id_category()
        # The validation function expects an id_number record. We don't have
        # that yet, so we'll mock one.
        IdNumber = namedtuple("ResPartnerIdNumber", ["name"])
        id_number = IdNumber(national_number)
        try:
            belgian_cat.validate_id_number(id_number)
        except ValidationError:
            if error:
                raise
            return False
        return True

    def update_be_national_register_number(self, national_number):
        self.ensure_one()
        result = None
        existing = self.get_be_national_register_number_id_number()
        # Update
        if existing:
            if not national_number:
                existing.unlink()
            else:
                existing.name = national_number
                result = existing
        # Create new
        elif national_number:
            values = {
                "name": national_number,
                "category_id": self.get_be_national_register_number_id_category().id,
                "partner_id": self.id,
            }
            result = self.env["res.partner.id_number"].create(values)
        return result
