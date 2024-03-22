# SPDX-FileCopyrightText: 2017 Open Architects Consulting SPRL
# SPDX-FileCopyrightText: 2018 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later
from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

TYPE_MAP = {
    "subscription": "subscribed",
    "transfer": "transfered",
    "sell_back": "resold",
}

TAX_SHELTER_TYPES = {
    "scale_up": {
        "name": _("Scale-up"),
        "percentage": 25,
        "capital_limit": 1000000,
    },
    "start_up_small": {
        "name": _("Start-up (small company)"),
        "percentage": 30,
        "capital_limit": 500000,
    },
    "start_up_micro": {
        "name": _("Start-up (micro company)"),
        "percentage": 45,
        "capital_limit": 500000,
    },
}


class TaxShelterDeclaration(models.Model):
    _name = "tax.shelter.declaration"
    _description = "Tax Shelter Declaration"

    name = fields.Char(
        string="Declaration year",
        required=True,
        compute="_compute_years",
        readonly=False,
    )
    fiscal_year = fields.Integer(
        required=True, compute="_compute_years", readonly=False
    )
    tax_shelter_certificates = fields.One2many(
        "tax.shelter.certificate",
        "declaration_id",
        readonly=True,
    )
    date_from = fields.Date(required=True, default=date(date.today().year - 1, 1, 1))
    date_to = fields.Date(required=True, default=date(date.today().year - 1, 12, 31))
    tax_shelter_type = fields.Selection("_get_tax_shelter_types", required=True)
    tax_shelter_percentage = fields.Float(
        compute="_compute_tax_shelter_percentage", digits=(3, 0)
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("computed", "Computed"),
            ("validated", "Validated"),
        ],
        required=True,
        default="draft",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        change_default=True,
        readonly=True,
        default=lambda self: self.env.company,
    )
    tax_shelter_capital_limit = fields.Float(
        string="Tax shelter capital limit",
        required=True,
        compute="_compute_tax_shelter_capital_limit",
        default=500000,
        readonly=False,
        store=True,
    )
    previously_subscribed_capital = fields.Float(
        string="Capital previously subscribed", readonly=True
    )
    excluded_cooperator = fields.Many2many(
        "res.partner",
        domain=[("cooperator", "=", True)],
        help="If these cooperator have"
        " subscribed share during the time"
        " frame of this Tax Shelter "
        "Declaration. They will be marked "
        "as non eligible",
    )

    def _get_tax_shelter_types(self):
        return [
            (k, _("{percentage}% - {name}").format(**v))
            for k, v in TAX_SHELTER_TYPES.items()
        ]

    @api.depends("tax_shelter_type")
    def _compute_tax_shelter_capital_limit(self):
        for record in self:
            tax_shelter_type = TAX_SHELTER_TYPES[record.tax_shelter_type]
            record.tax_shelter_capital_limit = tax_shelter_type["capital_limit"]

    @api.depends("tax_shelter_type")
    def _compute_tax_shelter_percentage(self):
        for record in self:
            tax_shelter_type = TAX_SHELTER_TYPES[record.tax_shelter_type]
            record.tax_shelter_percentage = tax_shelter_type["percentage"]

    @api.depends("date_from", "date_to")
    def _compute_years(self):
        for declaration in self:
            declaration.fiscal_year = declaration.date_from.year
            declaration.name = declaration.date_from.year + 1

    def _excluded_from_declaration(self, entry):
        if entry.date >= self.date_from and entry.date <= self.date_to:
            declaration = self
        else:
            declaration = self.search(
                [
                    ("date_from", "<=", entry.date),
                    ("date_to", ">=", entry.date),
                ]
            )
        if entry.partner_id.id in declaration.excluded_cooperator.ids:
            return True
        return False

    def _prepare_line(self, certificate, entry, ongoing_capital_sub, excluded):
        line_vals = {}
        line_vals["tax_shelter_certificate"] = certificate.id
        line_vals["share_type"] = entry.share_product_id.id
        line_vals["share_short_name"] = entry.share_short_name
        line_vals["share_unit_price"] = entry.share_unit_price
        line_vals["quantity"] = entry.quantity
        line_vals["transaction_date"] = entry.date
        line_vals["type"] = TYPE_MAP[entry.type]
        if entry.type == "subscription":
            if not excluded:
                capital_after_sub = ongoing_capital_sub + entry.total_amount_line
            else:
                capital_after_sub = ongoing_capital_sub
            line_vals["capital_before_sub"] = ongoing_capital_sub
            line_vals["capital_after_sub"] = capital_after_sub
            line_vals["capital_limit"] = self.tax_shelter_capital_limit
            if ongoing_capital_sub < self.tax_shelter_capital_limit and not excluded:
                line_vals["tax_shelter"] = True
        return line_vals

    def _compute_certificates(self, entries):
        partner_certificate = {}
        ongoing_capital_sub = 0.0
        for entry in entries:
            certificate = partner_certificate.get(entry.partner_id.id, False)

            if not certificate:
                # create a certificate for this cooperator
                cert_vals = {}
                cert_vals["declaration_id"] = self.id
                cert_vals["partner_id"] = entry.partner_id.id
                cert_vals[
                    "cooperator_number"
                ] = entry.partner_id.cooperator_register_number
                certificate = self.env["tax.shelter.certificate"].create(cert_vals)
                partner_certificate[entry.partner_id.id] = certificate
            excluded = self._excluded_from_declaration(entry)
            line_vals = self._prepare_line(
                certificate, entry, ongoing_capital_sub, excluded
            )
            certificate.write({"lines": [(0, 0, line_vals)]})

            if entry.type == "subscription" and not excluded:
                ongoing_capital_sub += entry.total_amount_line
        for certificate in partner_certificate.values():
            certificate.compute_not_eligible()
        return partner_certificate

    @api.constrains("date_from", "date_to")
    def _check_date_from_date_to(self):
        if self.date_from.year != self.date_to.year:
            raise ValidationError(_("Dates should belong in the same year."))
        if self.date_from > self.date_to:
            raise ValidationError(_("Date From should be before Date To."))

    def compute_declaration(self):
        self.ensure_one()
        entries = self.env["subscription.register"].search(
            [
                ("partner_id.is_company", "=", False),
                ("date", "<=", self.date_to),
                ("type", "in", ["subscription", "sell_back", "transfer"]),
            ]
        )

        subscriptions = entries.filtered(
            lambda r: r.type == "subscription" and r.date < self.date_from
        )  # noqa
        cap_prev_sub = 0.0
        for subscription in subscriptions:
            cap_prev_sub += subscription.total_amount_line

        self.previously_subscribed_capital = cap_prev_sub

        self._compute_certificates(entries)

        self.state = "computed"

    def validate_declaration(self):
        self.ensure_one()
        self.tax_shelter_certificates.filtered(lambda x: x.state == "draft").write(
            {"state": "validated"}
        )
        self.state = "validated"

    def reset_declaration(self):
        self.ensure_one()
        if not self.state == "validated":
            self.tax_shelter_certificates.unlink()
            self.state = "draft"
