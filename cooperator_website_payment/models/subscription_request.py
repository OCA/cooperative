# SPDX-FileCopyrightText: 2024 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import models


class SubscriptionRequest(models.Model):
    _name = "subscription.request"
    _inherit = ["subscription.request", "portal.mixin"]

    def _send_confirmation_mail(self):
        # this is an override to not send the confirmation email message
        # because subscription requests are automatically confirmed so that
        # they can be paid for.
        pass
