# Copyright 2022 Coop IT Easy SC
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Cooperators Website reCAPTCHA",
    "summary": "Add reCAPTCHA to Subscription Request Form",
    "version": "12.0.1.1.0",
    "category": "Cooperative management",
    "website": "https://github.com/OCA/cooperative",
    "author": "Coop IT Easy SC, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        "cooperator_website",
        "portal_recaptcha",
    ],
    "data": [
        "views/subscription_template.xml",
    ],
}