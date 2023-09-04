# SPDX-FileCopyrightText: 2017 Open Architects Consulting SPRL
# SPDX-FileCopyrightText: 2018 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import api, fields, models


class TaxShelterCertificateLine(models.Model):
    _name = "certificate.line"
    _description = "Tax Shelter Certificate Line"

    declaration_id = fields.Many2one(
        related="tax_shelter_certificate.declaration_id", string="Declaration"
    )
    tax_shelter_certificate = fields.Many2one(
        "tax.shelter.certificate",
        string="Tax shelter certificate",
        ondelete="cascade",
        required=True,
    )
    share_type = fields.Many2one(
        "product.product", string="Share type", required=True, readonly=True
    )
    share_unit_price = fields.Float(string="Share price", required=True, readonly=True)
    quantity = fields.Integer(string="Number of shares", required=True, readonly=True)
    transaction_date = fields.Date(string="Transaction date")
    tax_shelter = fields.Boolean(string="Tax shelter eligible", readonly=True)
    type = fields.Selection(
        [
            ("subscribed", "Subscribed"),
            ("resold", "Resold"),
            ("transfered", "Transfered"),
            ("kept", "Kept"),
        ],
        required=True,
        readonly=True,
    )
    amount_subscribed = fields.Float(
        compute="_compute_totals", string="Amount subscribed", store=True
    )
    amount_subscribed_eligible = fields.Float(
        compute="_compute_totals",
        string="Amount subscribed eligible",
        store=True,
    )
    amount_resold = fields.Float(
        compute="_compute_totals", string="Amount resold", store=True
    )
    amount_transfered = fields.Float(
        compute="_compute_totals", string="Amount transfered", store=True
    )
    share_short_name = fields.Char(string="Share type name", readonly=True)
    capital_before_sub = fields.Float(
        string="Capital before subscription", readonly=True
    )
    capital_after_sub = fields.Float(string="Capital after subscription", readonly=True)
    capital_limit = fields.Float(string="Capital limit", readonly=True)

    @api.depends("quantity", "share_unit_price")
    def _compute_totals(self):
        for line in self:
            if line.type == "subscribed":
                line.amount_subscribed = line.share_unit_price * line.quantity
            if line.type == "subscribed" and line.tax_shelter:
                if (
                    line.capital_before_sub < line.capital_limit
                    and line.capital_after_sub >= line.capital_limit
                ):
                    line.amount_subscribed_eligible = (
                        line.capital_limit - line.capital_before_sub
                    )
                elif (
                    line.capital_before_sub < line.capital_limit
                    and line.capital_after_sub <= line.capital_limit
                ):
                    line.amount_subscribed_eligible = (
                        line.share_unit_price * line.quantity
                    )
                elif line.capital_before_sub >= line.capital_limit:
                    line.amount_subscribed_eligible = 0
            if line.type == "resold":
                line.amount_resold = line.share_unit_price * -(line.quantity)
            if line.type == "transfered":
                line.amount_transfered = line.share_unit_price * -(line.quantity)
