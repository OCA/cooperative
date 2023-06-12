# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    company = env.ref("base.main_company")
    # Use the existing and already-in-use sequences for company 1.
    if company:
        # Set sequences on company and company on sequences
        # First sequence
        company.cooperator_subscription_sequence_id = env.ref(
            "cooperator.sequence_subscription"
        )
        company.cooperator_subscription_sequence_id.company_id = company
        # Second sequence
        company.cooperator_register_operation_sequence_id = env.ref(
            "cooperator.sequence_register_operation"
        )
        company.cooperator_register_operation_sequence_id.company_id = company
    other_companies = env["res.company"].search([]) - company
    other_companies._create_cooperator_sequences()
