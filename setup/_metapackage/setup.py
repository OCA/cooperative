import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-cooperative",
    description="Meta package for oca-cooperative Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-cooperator',
        'odoo14-addon-cooperator_portal',
        'odoo14-addon-cooperator_website',
        'odoo14-addon-l10n_be_cooperator',
        'odoo14-addon-l10n_be_cooperator_national_number',
        'odoo14-addon-l10n_be_cooperator_portal',
        'odoo14-addon-l10n_es_cooperator',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 14.0',
    ]
)
