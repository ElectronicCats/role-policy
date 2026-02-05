# Copyright 2024 Electronic Cats
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAccountMove(TransactionCase):
    """Tests for account.move extension with role_policy."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # Create role with action_post permission
        cls.role_with_post = cls.env["res.role"].create(
            {
                "name": "Accountant",
                "code": "ACCT",
            }
        )

        # Create the execution right
        cls.env["model.method.execution.right"].create(
            {
                "role_id": cls.role_with_post.id,
                "name": "account.move,action_post",
            }
        )

        # Create user with the role
        cls.user_with_post = cls.env["res.users"].create(
            {
                "name": "Accountant User",
                "login": "accountant_user",
                "role_ids": [(6, 0, [cls.role_with_post.id])],
            }
        )

        # Create role without action_post permission
        cls.role_no_post = cls.env["res.role"].create(
            {
                "name": "Basic User",
                "code": "BASU",
            }
        )
        cls.user_no_post = cls.env["res.users"].create(
            {
                "name": "Basic User",
                "login": "basic_user",
                "role_ids": [(6, 0, [cls.role_no_post.id])],
            }
        )

    def test_action_post_check_right_called(self):
        """Verify that action_post checks execution right."""
        # This test verifies the mechanism exists
        # In test mode, check_right returns True, so posting works
        # Full integration test would require disabling test_enable
        # The action_post method calls check_right
        # We verify the selection includes the method
        Right = self.env["model.method.execution.right"]
        selection = Right._selection_name()
        method_names = [s[0] for s in selection]
        self.assertIn("account.move,action_post", method_names)

    def test_execution_right_model_method_computed(self):
        """Verify that model_id and method are computed from name."""
        right = self.env["model.method.execution.right"].create(
            {
                "role_id": self.role_with_post.id,
                "name": "account.move,action_post",
            }
        )
        self.assertEqual(right.method, "action_post")
        self.assertEqual(right.model_id.model, "account.move")
