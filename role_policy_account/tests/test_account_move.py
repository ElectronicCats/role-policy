# Copyright 2024 Electronic Cats
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import unittest.mock

from odoo.addons.role_policy.tests.common import RolePolicyTestCommon
from odoo.exceptions import UserError
from odoo.tests.common import tagged


@tagged("post_install", "-at_install")
class TestAccountMove(RolePolicyTestCommon):
    """Tests for account.move extension with role_policy."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Grant action_post execution right to the common role
        cls.env["model.method.execution.right"].create(
            {
                "role_id": cls.role.id,
                "name": "account.move,action_post",
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
        """Verify that action_post checks execution right.

        Verifies the execution right is registered; actual denial is tested
        in test_action_post_raises_without_right.
        """
        Right = self.env["model.method.execution.right"]
        selection = Right._selection_name()
        method_names = [s[0] for s in selection]
        self.assertIn("account.move,action_post", method_names)

    def test_execution_right_model_method_computed(self):
        """Verify that model_id and method are computed from name."""
        right = self.env["model.method.execution.right"].create(
            {
                "role_id": self.role.id,
                "name": "account.move,action_post",
            }
        )
        self.assertEqual(right.method, "action_post")
        self.assertEqual(right.model_id.model, "account.move")

    def test_action_post_raises_without_right(self):
        """Verify that action_post raises UserError when user has no execution right."""
        journal = self.env["account.journal"].search([("type", "=", "sale")], limit=1)
        if not journal:
            self.skipTest("No sale journal found; account demo data required.")
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.env.ref("base.res_partner_1").id,
                "journal_id": journal.id,
            }
        )
        self.assertEqual(move.state, "draft")
        # With test_enable=True, check_right always returns True. Patch it so
        # the real ACL check runs and denies user_no_post.
        with unittest.mock.patch(
            "odoo.addons.role_policy.models.model_method_execution_right.config"
        ) as mock_config:
            mock_config.get.return_value = False
            with self.assertRaises(UserError):
                move.with_user(self.user_no_post).action_post()
