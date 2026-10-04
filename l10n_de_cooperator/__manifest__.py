# SPDX-FileCopyrightText: 2025 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

{
    "name": "Cooperators Germany",
    "summary": "German localization for Cooperators module",
    "version": "16.0.2.0.0",
    "category": "Cooperative management",
    "website": "https://github.com/OCA/cooperative",
    "author": "Coop IT Easy SC, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        "cooperator_website",
        "l10n_de",
        "l10n_de_partner_company_type",
    ],
    "data": [
        "views/subscription_template.xml",
    ],
    "auto_install": True,
}
