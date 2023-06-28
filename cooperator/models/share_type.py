# Copyright 2023 Coop IT Easy SC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


def get_share_types(env):
    shares = env["product.product"].search([("is_share", "=", True)])
    return [(s.default_code, s.short_name) for s in shares]
