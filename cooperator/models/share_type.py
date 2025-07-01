# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later


def get_share_types(env):
    # sudo needed for public access (for example, when submitting the
    # subscription form), when evaluating a model (for example,
    # cooperative.membership.cooperator_type, which uses this function to
    # determine the possible selection values).
    shares = env["product.product"].sudo().search([("is_share", "=", True)])
    return [(s.default_code, s.short_name) for s in shares]
