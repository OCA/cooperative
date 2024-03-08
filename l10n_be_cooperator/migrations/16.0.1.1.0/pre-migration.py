# SPDX-FileCopyrightText: 2024 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later


def migrate(cr, version):
    cr.execute(
        """
        ALTER TABLE tax_shelter_declaration
        ADD COLUMN tax_shelter_type character varying
        """,
    )
    cr.execute(
        """
        UPDATE tax_shelter_declaration
            SET tax_shelter_type = CASE
                WHEN tax_shelter_percentage = '25' THEN 'scale_up'
                WHEN tax_shelter_percentage = '30' THEN 'start_up_small'
                WHEN tax_shelter_percentage = '45' THEN 'start_up_micro'
            END
        """,
    )
