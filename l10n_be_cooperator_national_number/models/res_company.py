# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = "res.company"

    display_national_number = fields.Boolean()
    require_national_number = fields.Boolean()

    @api.constrains("display_national_number", "require_national_number")
    def _check_national_number(self):
        for company in self:
            if company.require_national_number and not company.display_national_number:
                raise ValidationError(
                    _(
                        'If the "Require National Number" toggle is enabled,'
                        ' then so must the "Display National Number" toggle.'
                    )
                )

    def get_display_national_number(self, is_company):
        self.ensure_one()
        if is_company:
            return False
        return self.display_national_number

    def get_require_national_number(self, is_company):
        self.ensure_one()
        if is_company:
            return False
        return self.require_national_number

    @api.onchange("display_national_number")
    def _onchange_display_national_number(self):
        if not self.display_national_number:
            self.require_national_number = False
