# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later


def get_share_types(env):
    shares = env["product.product"].search([("is_share", "=", True)])
    return [(s.default_code, s.short_name) for s in shares]
