# SPDX-FileCopyrightText: 2025 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later


def migrate(cr, version):
    # temp column to keep the values of legal_form after we removed it
    cr.execute(
        """
        ALTER TABLE res_partner
        RENAME COLUMN legal_form to legal_form_deprecated;
        """
    )

    # same operations for subscription_request
    cr.execute(
        """
        ALTER TABLE subscription_request
        RENAME COLUMN company_type to company_type_deprecated;
        """
    )
