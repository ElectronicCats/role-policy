# Copyright 2024 Electronic Cats
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.role_policy.models.helpers import (
    diff_to_odoo_x2many_commands,
    filter_odoo_x2many_commands,
    play_odoo_x2x_commands_on_ids,
)
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestHelpers(TransactionCase):
    """Tests for helper functions in helpers.py."""

    def test_filter_x2many_commands_command_4(self):
        """Test filter with command 4 (link)."""
        commands = [(4, 1), (4, 2), (4, 3)]
        keep_ids = [1, 3]
        result = filter_odoo_x2many_commands(commands, keep_ids)
        self.assertEqual(result, [(4, 1), (4, 3)])

    def test_filter_x2many_commands_command_6(self):
        """Test filter with command 6 (replace all)."""
        commands = [(6, 0, [1, 2, 3, 4, 5])]
        keep_ids = [2, 4]
        result = filter_odoo_x2many_commands(commands, keep_ids)
        self.assertEqual(result, [(6, 0, [2, 4])])

    def test_filter_x2many_commands_command_3(self):
        """Test filter with command 3 (unlink)."""
        commands = [(3, 1), (3, 2)]
        keep_ids = [1]
        result = filter_odoo_x2many_commands(commands, keep_ids)
        self.assertEqual(result, [(3, 1)])

    def test_filter_x2many_commands_command_1(self):
        """Test filter with command 1 (update)."""
        commands = [(1, 1, {"name": "test"}), (1, 2, {"name": "test2"})]
        keep_ids = [2]
        result = filter_odoo_x2many_commands(commands, keep_ids)
        self.assertEqual(result, [(1, 2, {"name": "test2"})])

    def test_filter_x2many_commands_command_2(self):
        """Test filter with command 2 (delete)."""
        commands = [(2, 1), (2, 2)]
        keep_ids = [1]
        result = filter_odoo_x2many_commands(commands, keep_ids)
        self.assertEqual(result, [(2, 1)])

    def test_filter_x2many_commands_command_0(self):
        """Test filter with command 0 (create) - should be preserved."""
        commands = [(0, 0, {"name": "new"})]
        keep_ids = [1, 2]
        result = filter_odoo_x2many_commands(commands, keep_ids)
        self.assertEqual(result, [(0, 0, {"name": "new"})])

    def test_filter_x2many_commands_empty_keep_ids(self):
        """Test filter with empty keep_ids."""
        commands = [(4, 1), (4, 2), (6, 0, [1, 2, 3])]
        keep_ids = []
        result = filter_odoo_x2many_commands(commands, keep_ids)
        self.assertEqual(result, [])

    def test_diff_to_x2many_commands_additions(self):
        """Test diff with additions only."""
        current_ids = [1, 2]
        target_ids = [1, 2, 3, 4]
        result = diff_to_odoo_x2many_commands(current_ids, target_ids)
        self.assertIn((4, 3), result)
        self.assertIn((4, 4), result)
        self.assertEqual(len(result), 2)

    def test_diff_to_x2many_commands_removals(self):
        """Test diff with removals only."""
        current_ids = [1, 2, 3]
        target_ids = [1]
        result = diff_to_odoo_x2many_commands(current_ids, target_ids)
        self.assertIn((3, 2), result)
        self.assertIn((3, 3), result)
        self.assertEqual(len(result), 2)

    def test_diff_to_x2many_commands_mixed(self):
        """Test diff with both additions and removals."""
        current_ids = [1, 2, 3]
        target_ids = [2, 3, 4, 5]
        result = diff_to_odoo_x2many_commands(current_ids, target_ids)
        # Should add 4, 5 and remove 1
        self.assertIn((4, 4), result)
        self.assertIn((4, 5), result)
        self.assertIn((3, 1), result)
        self.assertEqual(len(result), 3)

    def test_diff_to_x2many_commands_no_changes(self):
        """Test diff with no changes."""
        current_ids = [1, 2, 3]
        target_ids = {1, 2, 3}
        result = diff_to_odoo_x2many_commands(current_ids, target_ids)
        self.assertEqual(result, [])

    def test_diff_to_x2many_commands_empty_current(self):
        """Test diff with empty current ids."""
        current_ids = []
        target_ids = [1, 2]
        result = diff_to_odoo_x2many_commands(current_ids, target_ids)
        self.assertIn((4, 1), result)
        self.assertIn((4, 2), result)

    def test_diff_to_x2many_commands_empty_target(self):
        """Test diff with empty target ids."""
        current_ids = [1, 2]
        target_ids = []
        result = diff_to_odoo_x2many_commands(current_ids, target_ids)
        self.assertIn((3, 1), result)
        self.assertIn((3, 2), result)

    def test_play_x2x_commands_command_3(self):
        """Test play with command 3 (unlink)."""
        in_ids = {1, 2, 3}
        commands = [(3, 2)]
        result = play_odoo_x2x_commands_on_ids(in_ids, commands)
        self.assertEqual(result, {1, 3})

    def test_play_x2x_commands_command_4(self):
        """Test play with command 4 (link)."""
        in_ids = {1, 2}
        commands = [(4, 3)]
        result = play_odoo_x2x_commands_on_ids(in_ids, commands)
        self.assertEqual(result, {1, 2, 3})

    def test_play_x2x_commands_command_5(self):
        """Test play with command 5 (clear)."""
        in_ids = {1, 2, 3}
        commands = [(5,)]
        result = play_odoo_x2x_commands_on_ids(in_ids, commands)
        self.assertEqual(result, set())

    def test_play_x2x_commands_command_6(self):
        """Test play with command 6 (replace)."""
        in_ids = {1, 2, 3}
        commands = [(6, 0, [4, 5])]
        result = play_odoo_x2x_commands_on_ids(in_ids, commands)
        self.assertEqual(result, {4, 5})

    def test_play_x2x_commands_multiple_commands(self):
        """Test play with multiple commands."""
        in_ids = {1, 2, 3}
        commands = [(3, 1), (4, 4), (3, 2)]
        result = play_odoo_x2x_commands_on_ids(in_ids, commands)
        self.assertEqual(result, {3, 4})

    def test_play_x2x_commands_unsupported_raises(self):
        """Test play with unsupported command raises error."""
        in_ids = {1, 2}
        commands = [(0, 0, {"name": "test"})]  # Create command
        with self.assertRaises(NotImplementedError):
            play_odoo_x2x_commands_on_ids(in_ids, commands)

    def test_play_x2x_commands_command_1_raises(self):
        """Test play with command 1 (update) raises error."""
        in_ids = {1, 2}
        commands = [(1, 1, {"name": "test"})]
        with self.assertRaises(NotImplementedError):
            play_odoo_x2x_commands_on_ids(in_ids, commands)

    def test_play_x2x_commands_command_2_raises(self):
        """Test play with command 2 (delete) raises error."""
        in_ids = {1, 2}
        commands = [(2, 1)]
        with self.assertRaises(NotImplementedError):
            play_odoo_x2x_commands_on_ids(in_ids, commands)
