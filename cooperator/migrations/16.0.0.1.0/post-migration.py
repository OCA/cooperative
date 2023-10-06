# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from openupgradelib import openupgrade

_translations_to_delete = [
    "email_template_release_capital",
    "email_template_confirmation",
    "email_template_waiting_list",
    "email_template_certificate",
    "email_template_share_increase",
    "email_template_share_transfer",
    "email_template_share_update",
]

_records_to_delete = [
    "cooperator.email_template_confirmation_company",
]

# these act_windows had previously a domain set. simply removing the field
# element from the xml definition is not enough to reset it to its default
# value. instead of forcing it to False in the xml, they are reset in this
# script.
_act_windows_with_obsolete_domain = [
    "cooperator.action_partner_cooperator_form",
    "cooperator.action_partner_cooperator_candidate_form",
    "cooperator.action_company_representative_form",
]


def remove_act_windows_domain(env, act_window_xml_ids):
    for xml_id in act_window_xml_ids:
        act = env.ref(xml_id, raise_if_not_found=False)
        if not act:
            continue
        act.domain = False


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.load_data(env.cr, "cooperator", "data/mail_template_data.xml")
    openupgrade.delete_record_translations(
        env.cr, "cooperator", _translations_to_delete
    )
    openupgrade.delete_records_safely_by_xml_id(env, _records_to_delete)
    remove_act_windows_domain(env, _act_windows_with_obsolete_domain)
