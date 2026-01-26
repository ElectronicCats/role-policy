import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo18-addons-oca-role-policy",
    description="Meta package for oca-role-policy Odoo addons",
    version=version,
    install_requires=[
        'odoo18-addon-role_policy',
        'odoo18-addon-role_policy_account',
        'odoo18-addon-role_policy_demo',
        'odoo18-addon-role_policy_hr',
        'odoo18-addon-role_policy_hr_expense',
        'odoo18-addon-role_policy_sale',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 18.0',
    ]
)
