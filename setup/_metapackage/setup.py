import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-cooperative",
    description="Meta package for oca-cooperative Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-cooperator>=16.0dev,<16.1dev',
        'odoo-addon-cooperator_documentation>=16.0dev,<16.1dev',
        'odoo-addon-cooperator_portal>=16.0dev,<16.1dev',
        'odoo-addon-cooperator_website>=16.0dev,<16.1dev',
        'odoo-addon-l10n_be_cooperator>=16.0dev,<16.1dev',
        'odoo-addon-l10n_be_cooperator_national_number>=16.0dev,<16.1dev',
        'odoo-addon-l10n_be_cooperator_portal>=16.0dev,<16.1dev',
        'odoo-addon-l10n_be_cooperator_portal_national_number>=16.0dev,<16.1dev',
        'odoo-addon-l10n_be_cooperator_website_national_number>=16.0dev,<16.1dev',
        'odoo-addon-l10n_es_cooperator>=16.0dev,<16.1dev',
        'odoo-addon-l10n_fr_cooperator>=16.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 16.0',
    ]
)
