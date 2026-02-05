# Copyright 2024 Electronic Cats
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class RolePolicyTestCommon(TransactionCase):
    """Base class with shared test data for role_policy tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # Create test role
        cls.role = cls.env["res.role"].create(
            {
                "name": "Test Role",
                "code": "TEST",
            }
        )

        # Create test user with the role
        cls.test_user = cls.env["res.users"].create(
            {
                "name": "Test User",
                "login": "test_role_user",
                "email": "test@example.com",
                "role_ids": [(6, 0, [cls.role.id])],
            }
        )

        # Get test model (res.partner is always available)
        cls.partner_model = cls.env["ir.model"].search(
            [("model", "=", "res.partner")], limit=1
        )

        # Get a form view for testing
        cls.partner_form_view = cls.env.ref("base.view_partner_form")

    def _create_role_with_acl(self, code, model_name, perms):
        """Helper to create a role with specific ACL.

        Args:
            code: Role code (5 chars max)
            model_name: Model name (e.g., 'res.partner')
            perms: String with permissions, e.g., 'crud', 'ru', 'r'

        Returns:
            res.role record
        """
        model = self.env["ir.model"].search([("model", "=", model_name)], limit=1)
        role = self.env["res.role"].create(
            {
                "name": f"Role {code}",
                "code": code,
            }
        )
        self.env["res.role.acl"].create(
            {
                "role_id": role.id,
                "model_id": model.id,
                "perm_create": "c" in perms,
                "perm_read": "r" in perms,
                "perm_write": "u" in perms,
                "perm_unlink": "d" in perms,
            }
        )
        return role
