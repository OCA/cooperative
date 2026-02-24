# SPDX-FileCopyrightText: 2018 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import models


class SubscriptionRequest(models.Model):
    _inherit = "subscription.request"

    def get_required_field(self):
        req_fields = super().get_required_field()
        if "iban" in req_fields:
            req_fields.remove("iban")

        return req_fields

    def check_iban(self, iban):
        if iban:
            return super().check_iban(iban)
        return True
