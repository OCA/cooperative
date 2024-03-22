# SPDX-FileCopyrightText: 2013 - 2018 Open Architects Consulting SPRL
# SPDX-FileCopyrightText: 2018 Coop IT Easy SC
# SPDX-FileContributor: Houssine BAKKALI <houssine@coopiteasy.be>
# SPDX-FileContributor: Elouan Le Bars <elouan@coopiteasy.be>
# SPDX-FileContributor: Rémy Taymans <remy@coopiteasy.be>
# SPDX-FileContributor: Manuel Claeys Bouuaert <manuel@coopiteasy.be>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

{
    "name": "Cooperators Belgium",
    "summary": "Cooperators Belgium Localization",
    "version": "16.0.1.2.0",
    "depends": [
        "cooperator",
        "cooperator_website",
        "l10n_be",
    ],
    "author": "Coop IT Easy SC, Odoo Community Association (OCA)",
    "category": "Cooperative management",
    "website": "https://github.com/OCA/cooperative",
    "license": "AGPL-3",
    "data": [
        "security/ir.model.access.csv",
        "report/tax_shelter_report.xml",
        "report/tax_shelter_report_templates.xml",
        "report/tax_shelter_subscription_report.xml",
        "report/tax_shelter_shares_report.xml",
        "views/tax_shelter_declaration_view.xml",
        "views/subscription_template.xml",
        "data/mail_template_data.xml",
        "data/scheduler_data.xml",
    ],
    "demo": [
        "demo/tax_shelter_demo.xml",
    ],
    "auto_install": True,
}
