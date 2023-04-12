{
    "name": "Account Banking Mandate Cooperator",
    "version": "14.0.1.0.1",
    "license": "AGPL-3",
    "summary": """
        This module adds mandate selection to cooperator subscription request.""",
    "author": "Som IT SCCL, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/cooperative",
    "category": "Banking addons",
    "depends": ["cooperator", "account_payment_cooperator", "account_banking_mandate"],
    "data": [
        "views/subscription_request_views.xml",
    ],
    "installable": True,
}
