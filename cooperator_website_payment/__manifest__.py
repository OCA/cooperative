# SPDX-FileCopyrightText: 2024 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

{
    "name": "Cooperator Website Payment",
    "summary": "Enable direct online payment of cooperative shares",
    "version": "16.0.1.0.0",
    "category": "Cooperative management",
    "website": "https://github.com/OCA/cooperative",
    "author": "Coop IT Easy SC, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        "cooperator_website",
        "website_payment",
    ],
    "data": [
        "views/report_invoice.xml",
        "views/website_templates.xml",
    ],
}
