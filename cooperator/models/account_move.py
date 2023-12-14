# SPDX-FileCopyrightText: 2019 Coop IT Easy SC
# SPDX-FileContributor: Houssine Bakkali <houssine@coopiteasy.be>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from datetime import datetime

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"
    _check_company_auto = True

    subscription_request = fields.Many2one(
        "subscription.request",
        string="Subscription request",
        check_company=True,
    )
    release_capital_request = fields.Boolean(string="Release of capital request")

    def _get_starting_sequence(self):
        self.ensure_one()
        if not self.release_capital_request:
            return super()._get_starting_sequence()
        starting_sequence = "%s/%04d/000" % (self.journal_id.code, self.date.year)
        if self.journal_id.refund_sequence and self.move_type in (
            "out_refund",
            "in_refund",
        ):
            starting_sequence = "R" + starting_sequence
        return starting_sequence

    def get_mail_template_certificate(self):
        if self.partner_id.member:
            return self.company_id.get_cooperator_certificate_increase_mail_template()
        return self.company_id.get_cooperator_certificate_mail_template()

    def get_share_line_vals(self, line, effective_date):
        return {
            "share_number": line.quantity,
            "share_product_id": line.product_id.id,
            "partner_id": self.partner_id.id,
            "share_unit_price": line.price_unit,
            "effective_date": effective_date,
            "company_id": self.company_id.id,
        }

    def get_subscription_register_vals(self, line, effective_date):
        return {
            "partner_id": self.partner_id.id,
            "quantity": line.quantity,
            "share_product_id": line.product_id.id,
            "share_unit_price": line.price_unit,
            "date": effective_date,
            "type": "subscription",
            "company_id": self.company_id.id,
        }

    def _send_certificate_mail(self, certificate_email_template, sub_reg_line):
        if self.company_id.send_certificate_email:
            # we send the email with the certificate in attachment
            certificate_email_template.sudo().send_mail(
                self.partner_id.id, email_layout_xmlid="mail.mail_notification_layout"
            )

    def set_cooperator_effective(self, effective_date):
        sub_register_obj = self.env["subscription.register"]
        share_line_obj = self.env["share.line"]

        certificate_email_template = self.get_mail_template_certificate()

        self.partner_id.get_cooperative_membership(self.company_id).set_effective()

        sub_reg_operation = self.company_id.get_next_register_operation_number()

        for line in self.invoice_line_ids:
            sub_reg_vals = self.get_subscription_register_vals(line, effective_date)
            sub_reg_vals["name"] = sub_reg_operation
            sub_reg_vals["register_number_operation"] = int(sub_reg_operation)

            sub_reg_line = sub_register_obj.create(sub_reg_vals)

            share_line_vals = self.get_share_line_vals(line, effective_date)
            share_line_obj.create(share_line_vals)

            if line.product_id.mail_template:
                certificate_email_template = line.product_id.mail_template

        self._send_certificate_mail(certificate_email_template, sub_reg_line)

        return True

    def post_process_confirm_paid(self, effective_date):
        self.set_cooperator_effective(effective_date)

        return True

    def get_refund_domain(self, invoice):
        return [
            ("move_type", "=", "out_refund"),
            ("invoice_origin", "=", invoice.name),
        ]

    def _get_payment_account_moves(self):
        reconciled_lines = self.line_ids.filtered(
            lambda line: line.account_id.account_type == "asset_receivable"
        )
        reconciled_amls = reconciled_lines.mapped("matched_credit_ids.credit_move_id")
        return reconciled_amls.move_id

    def _invoice_paid_hook(self):
        result = super()._invoice_paid_hook()
        for invoice in self:
            cooperative_membership = invoice.partner_id.get_cooperative_membership(
                invoice.company_id
            )
            if not (
                invoice.move_type == "out_invoice"
                and invoice.release_capital_request
                and cooperative_membership
                and cooperative_membership.cooperator
            ):
                continue

            # we check if there is an open refund for this invoice. in this
            # case we don't run the process_subscription function as the
            # invoice has been reconciled with a refund and not a payment.
            domain = self.get_refund_domain(invoice)
            refund = self.search(domain)
            if refund:
                # if there is a open refund we mark the subscription as cancelled
                invoice.subscription_request.state = "cancelled"
            else:
                # take the effective date from the payment.
                # by default the confirmation date is the payment date
                effective_date = datetime.now()

                payment_moves = [am for am in self._get_payment_account_moves()]
                if payment_moves:
                    payment_moves.sort(key=lambda p: p.date)
                    effective_date = payment_moves[-1].date

                invoice.subscription_request.state = "paid"
                invoice.post_process_confirm_paid(effective_date)
        return result

    def _get_capital_release_mail_template(self):
        return self.company_id.get_cooperator_capital_release_mail_template()

    def send_capital_release_request_mail(self):
        if self.company_id.send_capital_release_email:
            email_template = self._get_capital_release_mail_template()
            # we send the email with the capital release request in attachment
            # TODO remove sudo() and give necessary access right
            email_template.sudo().send_mail(
                self.id, email_layout_xmlid="mail.mail_notification_layout"
            )
