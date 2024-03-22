# SPDX-FileCopyrightText: 2017 Open Architects Consulting SPRL
# SPDX-FileCopyrightText: 2018 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import base64

from odoo import api, fields, models

REPORTS = {
    "subscription": (
        "l10n_be_cooperator.action_tax_shelter_subscription_report",
        "Tax Shelter Subscription",
    ),
    "shares": (
        "l10n_be_cooperator.action_tax_shelter_shares_report",
        "Tax Shelter Shares",
    ),
}


def send_mail_with_additional_attachments(mail_template, res_id, attachments):
    # FIXME: this is a workaround to allow to add multiple attachments to a
    # mail message sent from a mail template. the
    # mail_template_multi_attachment module should be used instead, but it is
    # currently only available in version 13.0.

    # .send_mail() creates a mail message but does not send it yet. it will be
    # sent later when the email queue will be processed.
    message_id = mail_template.send_mail(
        res_id, email_layout_xmlid="mail.mail_notification_layout"
    )
    env = mail_template.env
    message = env["mail.mail"].browse(message_id)
    attachment_model = env["ir.attachment"]
    attachment_ids = [attachment.id for attachment in message.attachment_ids]
    for attachment in attachments:
        attachment_data = {
            "name": attachment[0],
            "datas": attachment[1],
            "type": "binary",
            "res_model": "mail.message",
            "res_id": message.mail_message_id.id,
        }
        attachment_ids.append(attachment_model.create(attachment_data).id)
    message.attachment_ids = [(6, 0, attachment_ids)]


class TaxShelterCertificate(models.Model):
    _name = "tax.shelter.certificate"
    _inherit = ["portal.mixin"]
    _description = "Tax Shelter Certificate"
    _order = "cooperator_number asc"

    cooperator_number = fields.Integer(
        string="Cooperator number", required=True, readonly=True
    )
    partner_id = fields.Many2one(
        "res.partner", string="Cooperator", required=True, readonly=True
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("validated", "Validated"),
            ("not_eligible", "Not Eligible"),
            ("sent", "Sent"),
        ],
        required=True,
        default="draft",
    )
    declaration_id = fields.Many2one(
        "tax.shelter.declaration",
        string="Declaration",
        required=True,
        readonly=True,
        ondelete="restrict",
    )
    lines = fields.One2many(
        "certificate.line",
        "tax_shelter_certificate",
        string="Certificate lines",
        readonly=True,
    )
    previously_subscribed_lines = fields.One2many(
        compute="_compute_certificate_lines",
        comodel_name="certificate.line",
        string="Previously Subscribed lines",
        readonly=True,
    )
    previously_subscribed_eligible_lines = fields.One2many(
        compute="_compute_certificate_lines",
        comodel_name="certificate.line",
        string="Previously Subscribed eligible lines",
        readonly=True,
    )
    subscribed_lines = fields.One2many(
        compute="_compute_certificate_lines",
        comodel_name="certificate.line",
        string="Shares subscribed",
        readonly=True,
    )
    resold_lines = fields.One2many(
        compute="_compute_certificate_lines",
        comodel_name="certificate.line",
        string="Shares resold",
        readonly=True,
    )
    transfered_lines = fields.One2many(
        compute="_compute_certificate_lines",
        comodel_name="certificate.line",
        string="Shares transfered",
        readonly=True,
    )
    total_amount_previously_subscribed = fields.Float(
        compute="_compute_amounts", string="Total previously subscribed"
    )
    total_amount_eligible_previously_subscribed = fields.Float(
        compute="_compute_amounts",
        string="Total eligible previously subscribed",
    )
    total_amount_subscribed = fields.Float(
        compute="_compute_amounts", string="Total subscribed"
    )
    total_amount_eligible = fields.Float(
        compute="_compute_amounts",
        string="Total amount eligible To Tax shelter",
    )
    total_amount_resold = fields.Float(
        compute="_compute_amounts", string="Total resold"
    )
    total_amount_transfered = fields.Float(
        compute="_compute_amounts", string="Total transfered"
    )
    total_amount = fields.Float(
        compute="_compute_amounts", string="Total", readonly=True
    )
    company_id = fields.Many2one(related="declaration_id.company_id", string="Company")

    def _compute_access_url(self):
        result = super()._compute_access_url()
        for certificate in self:
            certificate.access_url = "/my/tax_shelter_certificates/%s" % (
                certificate.id
            )
        return result

    def generate_pdf_report(self, report_type):
        report, name = REPORTS[report_type]
        report = self.env.ref(report)._render_qweb_pdf(report, [self.id])[0]
        report = base64.b64encode(report)
        report_name = (
            self.partner_id.name + " " + name + " " + self.declaration_id.name + ".pdf"
        ).replace("/", "_")

        return (report_name, report)

    def generate_certificates_report(self):
        attachments = []
        if self.total_amount_eligible > 0:
            attachments.append(self.generate_pdf_report("subscription"))
        if self.partner_id.total_value > 0:
            attachments.append(self.generate_pdf_report("shares"))
        # if self.total_amount_resold > 0 or self.total_amount_transfered > 0:
        # TODO
        return attachments

    def send_certificates(self):
        tax_shelter_mail_template = self.env.ref(
            "l10n_be_cooperator.email_template_tax_shelter_certificate"
        )
        for certificate in self.filtered(lambda x: x.state in ("validated", "sent")):
            attachments = certificate.generate_certificates_report()
            if len(attachments) > 0:
                send_mail_with_additional_attachments(
                    tax_shelter_mail_template, certificate.id, attachments
                )
            certificate.state = "sent"

    def print_subscription_certificate(self):
        self.ensure_one()
        report, name = REPORTS["subscription"]
        return self.env.ref(report).report_action(self)

    def print_shares_certificate(self):
        self.ensure_one()
        report, name = REPORTS["shares"]
        return self.env.ref(report).report_action(self)

    def _compute_amounts(self):
        for certificate in self:
            total_amount_previously_subscribed = 0
            total_amount_previously_eligible = 0
            total_amount_subscribed = 0
            total_amount_eligible = 0
            total_amount_transfered = 0
            total_amount_resold = 0

            for line in certificate.subscribed_lines:
                total_amount_subscribed += line.amount_subscribed
                total_amount_eligible += line.amount_subscribed_eligible
            certificate.total_amount_subscribed = total_amount_subscribed
            certificate.total_amount_eligible = total_amount_eligible

            for line in certificate.previously_subscribed_eligible_lines:
                total_amount_previously_eligible += line.amount_subscribed_eligible
            certificate.total_amount_eligible_previously_subscribed = (
                total_amount_previously_eligible
            )

            for line in certificate.previously_subscribed_lines:
                total_amount_previously_subscribed += line.amount_subscribed
            certificate.total_amount_previously_subscribed = (
                total_amount_previously_subscribed
            )

            for line in certificate.transfered_lines:
                total_amount_transfered += line.amount_transfered
            certificate.total_amount_transfered = total_amount_transfered

            for line in certificate.resold_lines:
                total_amount_resold += line.amount_resold
            certificate.total_amount_resold = total_amount_resold
            certificate.total_amount = (
                certificate.total_amount_previously_subscribed
                + certificate.total_amount_subscribed
                + certificate.total_amount_resold
                + certificate.total_amount_transfered
            )

    def compute_not_eligible(self):
        if (
            self.total_amount_eligible
            + self.total_amount_eligible_previously_subscribed
            == 0
        ):
            self.state = "not_eligible"

    @api.depends("lines")
    def _compute_certificate_lines(self):
        for certificate in self:
            certificate.previously_subscribed_lines = certificate.lines.filtered(
                lambda r: r.type == "subscribed"
                and r.transaction_date < certificate.declaration_id.date_from
            )
            certificate.previously_subscribed_eligible_lines = (
                certificate.lines.filtered(  # noqa
                    lambda r: r.type == "subscribed"
                    and r.transaction_date < certificate.declaration_id.date_from
                    and r.tax_shelter
                )
            )
            certificate.subscribed_lines = certificate.lines.filtered(
                lambda r: r.type == "subscribed"
                and r.transaction_date >= certificate.declaration_id.date_from
                and r.transaction_date <= certificate.declaration_id.date_to
            )
            certificate.resold_lines = certificate.lines.filtered(
                lambda r: r.type == "resold"
                and r.transaction_date >= certificate.declaration_id.date_from
                and r.transaction_date <= certificate.declaration_id.date_to
            )
            certificate.transfered_lines = certificate.lines.filtered(
                lambda r: r.type == "transfered"
                and r.transaction_date >= certificate.declaration_id.date_from
                and r.transaction_date <= certificate.declaration_id.date_to
            )

    @api.model
    def batch_send_tax_shelter_certificate(self):
        certificates = self.search([("state", "=", "validated")], limit=80)
        certificates.send_certificates()
