import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo12-addons-oca-cooperative",
    description="Meta package for oca-cooperative Odoo addons",
    version=version,
    install_requires=[
        'odoo12-addon-cooperator',
        'odoo12-addon-cooperator_portal',
        'odoo12-addon-cooperator_website',
        'odoo12-addon-cooperator_website_referral_source',
        'odoo12-addon-l10n_be_cooperator',
        'odoo12-addon-l10n_be_cooperator_national_number',
        'odoo12-addon-l10n_be_cooperator_website_national_number',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 12.0',
    ]
)
