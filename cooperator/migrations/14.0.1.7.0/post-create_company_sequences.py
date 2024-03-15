# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def remove_xmlid(env, module, name):
    xmlid_record = env["ir.model.data"].search(
        [("module", "=", module), ("name", "=", name)]
    )
    if xmlid_record:
        xmlid_record.unlink()


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    company = env.ref("base.main_company")
    # Use the existing and already-in-use sequences for company 1.
    if company:
        cooperator_number = env.ref("cooperator.sequence_subscription")
        cooperator_number.write(
            {
                "company_id": company.id,
                "code": "cooperator.number",
            }
        )
        register_operation = env.ref("cooperator.sequence_register_operation")
        register_operation.write(
            {
                "company_id": company.id,
                "code": "register.operation",
            }
        )
        # Delete the xmlids. The actual records are preserved.
        remove_xmlid(env, "cooperator", "sequence_subscription")
        remove_xmlid(env, "cooperator", "sequence_register_operation")
    # Create sequences for other companies.
    other_companies = env["res.company"].search([]) - company
    if other_companies:
        other_companies._create_cooperator_sequences()
