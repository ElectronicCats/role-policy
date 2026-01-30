import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-role-policy",
    description="Meta package for oca-role-policy Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-role_policy',
        'odoo-addon-role_policy_account',
        'odoo-addon-role_policy_demo',
        'odoo-addon-role_policy_hr',
        'odoo-addon-role_policy_hr_expense',
        'odoo-addon-role_policy_sale',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 18.0',
    ]
)
