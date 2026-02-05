# Copyright 2024 Electronic Cats
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestUntouchableGroupsHRExpense(TransactionCase):
    """Tests for _role_policy_untouchable_groups in role_policy_hr_expense."""

    def test_hr_expense_group_in_untouchables(self):
        """Verify that hr_expense.group_hr_expense_team_approver is in untouchable groups."""
        # Use any model that inherits from 'base'
        untouchables = self.env["res.partner"]._role_policy_untouchable_groups()
        self.assertIn("hr_expense.group_hr_expense_team_approver", untouchables)

    def test_untouchable_groups_is_list(self):
        """Verify that _role_policy_untouchable_groups returns a list."""
        untouchables = self.env["res.partner"]._role_policy_untouchable_groups()
        self.assertIsInstance(untouchables, list)

    def test_hr_group_still_included(self):
        """Verify that hr.group_hr_user from role_policy_hr is also included."""
        # role_policy_hr_expense depends on role_policy_hr
        untouchables = self.env["res.partner"]._role_policy_untouchable_groups()
        self.assertIn("hr.group_hr_user", untouchables)
