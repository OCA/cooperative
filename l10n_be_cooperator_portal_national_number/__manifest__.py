# SPDX-FileCopyrightText: 2024 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

{
    "name": "Belgium: Cooperator Portal National Number",
    "summary": """
        Add the ability to change national number on the account portal.""",
    "version": "16.0.1.0.0",
    "category": "Cooperative management",
    "website": "https://github.com/OCA/cooperative",
    "author": "Coop IT Easy SC, Odoo Community Association (OCA)",
    "maintainers": ["carmenbianca"],
    "license": "AGPL-3",
    "application": False,
    "depends": [
        "cooperator_portal",
        "l10n_be_cooperator_national_number",
    ],
    "auto_install": True,
    "data": ["views/portal_templates.xml"],
}
