# Copyright 2024 Electronic Cats
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestModelMethodExecutionRightAccount(TransactionCase):
    """Tests for model.method.execution.right extension in role_policy_account."""

    def test_selection_name_includes_action_post(self):
        """Verify that _selection_name includes account.move,action_post."""
        Right = self.env["model.method.execution.right"]
        selection = Right._selection_name()
        method_names = [s[0] for s in selection]
        self.assertIn("account.move,action_post", method_names)

    def test_selection_name_is_sorted(self):
        """Verify that _selection_name returns sorted list."""
        Right = self.env["model.method.execution.right"]
        selection = Right._selection_name()
        method_names = [s[0] for s in selection]
        self.assertEqual(method_names, sorted(method_names))
