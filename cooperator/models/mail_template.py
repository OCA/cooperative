# SPDX-FileCopyrightText: 2019 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import fields, models


class MailTemplate(models.Model):
    _inherit = "mail.template"

    is_cooperator_template = fields.Boolean(string="Cooperator mail template")
