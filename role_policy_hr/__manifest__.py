# Copyright 2020-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Role Policy HR",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "Noviat, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/role-policy",
    "category": "Tools",
    "depends": ["hr", "role_policy"],
    "data": [],
    "assets": {
        "web.assets_backend": [
            "role_policy_hr/static/src/js/**/*",
        ],
    },
    "maintainers": ["luc-demeyer"],
    "installable": True,
    "auto_install": True,
}
