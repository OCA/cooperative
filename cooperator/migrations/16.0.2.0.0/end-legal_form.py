# SPDX-FileCopyrightText: 2025 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later


def migrate(cr, version):
    # remove temp column after l10n modules used it to map the previous values
    cr.execute(
        """
        ALTER TABLE res_partner
        DROP COLUMN legal_form_deprecated;
        """
    )

    # same operations for subscription_request
    cr.execute(
        """
        ALTER TABLE subscription_request
        DROP COLUMN company_type_deprecated;
        """
    )
