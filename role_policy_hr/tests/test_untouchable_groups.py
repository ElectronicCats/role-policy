# Copyright 2024 Electronic Cats
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestUntouchableGroupsHR(TransactionCase):
    """Tests for _role_policy_untouchable_groups in role_policy_hr."""

    def test_hr_group_in_untouchables(self):
        """Verify that hr.group_hr_user is in untouchable groups."""
        # Use any model that inherits from 'base'
        untouchables = self.env["res.partner"]._role_policy_untouchable_groups()
        self.assertIn("hr.group_hr_user", untouchables)

    def test_untouchable_groups_is_list(self):
        """Verify that _role_policy_untouchable_groups returns a list."""
        untouchables = self.env["res.partner"]._role_policy_untouchable_groups()
        self.assertIsInstance(untouchables, list)

    def test_untouchable_groups_includes_base_groups(self):
        """Verify that base untouchable groups are also included."""
        untouchables = self.env["res.partner"]._role_policy_untouchable_groups()
        # Base groups should include base.group_no_one at minimum
        self.assertIn("base.group_no_one", untouchables)
