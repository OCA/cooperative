# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    sql = """
        UPDATE res_company
        SET display_national_number = true
        WHERE require_national_number = true
    """
    openupgrade.logged_query(env.cr, sql)
