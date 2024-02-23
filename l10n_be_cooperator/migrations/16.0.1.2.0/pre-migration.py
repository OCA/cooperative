# SPDX-FileCopyrightText: 2024 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later


def migrate(cr, version):
    cr.execute(
        """
        UPDATE tax_shelter_certificate
            SET state = 'not_eligible'
                WHERE state = 'no_eligible'
        """,
    )
