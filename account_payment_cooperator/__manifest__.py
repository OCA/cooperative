{
    "name": "Account Payment Cooperator",
    "version": "14.0.1.0.1",
    "license": "AGPL-3",
    "summary": """
        This module adds support for payment mode to cooperator.""",
    "author": "Som IT SCCL, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/cooperative",
    "category": "Banking addons",
    "depends": ["cooperator", "account_payment_partner"],
    "data": [
        "views/product_template_views.xml",
        "views/subscription_request_views.xml",
    ],
    "installable": True,
}
