# Copyright 2026 PopSolutions
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Cooperator Brazil Localisation",
    "version": "18.0.1.0.0",
    "depends": ["cooperator", "cooperator_website", "l10n_br_base"],
    "author": "PopSolutions, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/cooperative",
    "category": "Cooperative management",
    "summary": "Localizacao brasileira do Cooperator: CPF/CNPJ e razao social",
    "license": "AGPL-3",
    "data": [
        "views/subscription_request_view.xml",
        "views/subscription_templates.xml",
    ],
    "installable": True,
    # Deliberadamente NAO auto_install: instalar de forma explicita.
    "auto_install": False,
}
