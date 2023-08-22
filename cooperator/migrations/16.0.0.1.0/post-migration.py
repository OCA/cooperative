# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from openupgradelib import openupgrade

_translations_to_delete = [
    "email_template_release_capital",
    "email_template_confirmation",
    "email_template_waiting_list",
    "email_template_certificat",
    "email_template_certificat_increase",
    "email_template_share_transfer",
    "email_template_share_update",
]

_records_to_delete = [
    "cooperator.email_template_confirmation_company",
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.load_data(env.cr, "cooperator", "data/mail_template_data.xml")
    openupgrade.delete_record_translations(
        env.cr, "cooperator", _translations_to_delete
    )
    openupgrade.delete_records_safely_by_xml_id(env, _records_to_delete)
