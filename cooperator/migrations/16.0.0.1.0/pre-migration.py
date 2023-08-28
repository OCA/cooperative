# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from openupgradelib import openupgrade

_xml_ids_renames = [
    (
        "cooperator.email_template_certificat",
        "cooperator.email_template_certificate",
    ),
    (
        "cooperator.email_template_certificat_increase",
        "cooperator.email_template_share_increase",
    ),
    (
        "cooperator.theme_invoice_G002",
        "cooperator.report_invoice",
    ),
    (
        "cooperator.theme_invoice_G002_document",
        "cooperator.report_invoice_document",
    ),
    (
        "cooperator.cooperator_subscription_G001",
        "cooperator.report_subscription_register",
    ),
    (
        "cooperator.action_cooperator_report_certificat",
        "cooperator.action_cooperator_report_certificate",
    ),
    (
        "cooperator.cooperator_certificat_G001",
        "cooperator.report_cooperator_certificate",
    ),
    (
        "cooperator.cooperator_certificat_G001_document",
        "cooperator.report_cooperator_certificate_document",
    ),
    (
        "cooperator.cooperator_register_G001",
        "cooperator.report_cooperator_register",
    ),
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_xmlids(env.cr, _xml_ids_renames)
