# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from openupgradelib import openupgrade

_translations_to_delete = [
    "email_template_tax_shelter_certificate",
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.load_data(env.cr, "l10n_be_cooperator", "data/mail_template_data.xml")
    openupgrade.delete_record_translations(
        env.cr, "l10n_be_cooperator", _translations_to_delete
    )
