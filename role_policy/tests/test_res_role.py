# Copyright 2024 Electronic Cats
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests.common import tagged

from .common import RolePolicyTestCommon


@tagged("post_install", "-at_install")
class TestResRole(RolePolicyTestCommon):
    """Tests for the res.role model."""

    def test_role_create_creates_group(self):
        """Verify that creating a role creates an associated group."""
        role = self.env["res.role"].create(
            {
                "name": "New Role",
                "code": "NEW",
            }
        )
        self.assertTrue(role.group_id, "Role should have an associated group")
        self.assertEqual(role.group_id.name, "NEW")
        self.assertTrue(role.group_id.role, "Group should be marked as role group")

    def test_role_create_with_users(self):
        """Verify that users are correctly assigned when creating a role."""
        user = self.env["res.users"].create(
            {
                "name": "Role Test User",
                "login": "role_test_user_create",
            }
        )
        role = self.env["res.role"].create(
            {
                "name": "User Role",
                "code": "USRR",
                "user_ids": [(6, 0, [user.id])],
            }
        )
        self.assertIn(user, role.user_ids)
        self.assertIn(role.group_id, user.groups_id)

    def test_role_write_update_users_command_6(self):
        """Verify that _update_role_groups works correctly with command 6."""
        user1 = self.env["res.users"].create(
            {
                "name": "User 1",
                "login": "user_1_role",
            }
        )
        user2 = self.env["res.users"].create(
            {
                "name": "User 2",
                "login": "user_2_role",
            }
        )
        self.role.write({"user_ids": [(6, 0, [user1.id])]})
        self.assertIn(user1, self.role.user_ids)

        # Change users
        self.role.write({"user_ids": [(6, 0, [user2.id])]})
        self.assertNotIn(user1, self.role.user_ids)
        self.assertIn(user2, self.role.user_ids)

    def test_role_write_update_users_command_4(self):
        """Verify that _update_role_groups works with command 4 (add)."""
        user = self.env["res.users"].create(
            {
                "name": "User Add",
                "login": "user_add_role",
            }
        )
        self.role.write({"user_ids": [(4, user.id)]})
        self.assertIn(user, self.role.user_ids)

    def test_role_write_code_with_acl_raises_error(self):
        """Verify that changing code is not allowed when ACLs exist."""
        # Create ACL for the role
        self.env["res.role.acl"].create(
            {
                "role_id": self.role.id,
                "model_id": self.partner_model.id,
                "perm_read": True,
            }
        )
        with self.assertRaises(UserError):
            self.role.write({"code": "NEWC"})

    def test_role_write_code_without_acl_allowed(self):
        """Verify that changing code is allowed when no ACLs exist."""
        role = self.env["res.role"].create(
            {
                "name": "Code Change Role",
                "code": "CHNG",
            }
        )
        role.write({"code": "NEWCD"})
        self.assertEqual(role.code, "NEWCD")

    def test_role_unlink_deletes_group(self):
        """Verify that deleting a role also deletes its associated group."""
        role = self.env["res.role"].create(
            {
                "name": "To Delete",
                "code": "DEL",
            }
        )
        group_id = role.group_id.id
        role.unlink()
        group = self.env["res.groups"].search([("id", "=", group_id)])
        self.assertFalse(group, "Group should be deleted with role")

    def test_role_menu_ids_updates_groups(self):
        """Verify that menu_ids updates groups_id of the menu."""
        menu = self.env["ir.ui.menu"].create(
            {
                "name": "Test Menu",
            }
        )
        self.role.write({"menu_ids": [(4, menu.id)]})
        self.assertIn(self.role.group_id, menu.groups_id)

        self.role.write({"menu_ids": [(3, menu.id)]})
        self.assertNotIn(self.role.group_id, menu.groups_id)

    def test_role_act_window_ids_updates_groups(self):
        """Verify that act_window_ids updates groups_id of the action."""
        action = self.env["ir.actions.act_window"].create(
            {
                "name": "Test Action",
                "res_model": "res.partner",
            }
        )
        self.role.write({"act_window_ids": [(4, action.id)]})
        # Note: ir.actions.actions.__getattribute__ filters role groups for
        # excluded users (admin). Use read() to bypass the filter.
        action_groups = action.read(["groups_id"])[0]["groups_id"]
        self.assertIn(self.role.group_id.id, action_groups)

    def test_role_act_window_ids_command_6(self):
        """Verify that act_window_ids with command 6 works correctly."""
        action1 = self.env["ir.actions.act_window"].create(
            {
                "name": "Test Action 1",
                "res_model": "res.partner",
            }
        )
        action2 = self.env["ir.actions.act_window"].create(
            {
                "name": "Test Action 2",
                "res_model": "res.partner",
            }
        )
        # First add action1
        self.role.write({"act_window_ids": [(4, action1.id)]})
        # Use read() to bypass __getattribute__ filter for admin
        action1_groups = action1.read(["groups_id"])[0]["groups_id"]
        self.assertIn(self.role.group_id.id, action1_groups)

        # Replace with action2
        self.role.write({"act_window_ids": [(6, 0, [action2.id])]})
        action1.invalidate_recordset()
        action2.invalidate_recordset()
        action1_groups = action1.read(["groups_id"])[0]["groups_id"]
        action2_groups = action2.read(["groups_id"])[0]["groups_id"]
        self.assertNotIn(self.role.group_id.id, action1_groups)
        self.assertIn(self.role.group_id.id, action2_groups)

    def test_role_code_unique_constraint(self):
        """Verify unique constraint on code per company."""
        with self.assertRaises(Exception):  # noqa: B017 IntegrityError wrapped
            self.env["res.role"].create(
                {
                    "name": "Duplicate Code",
                    "code": "TEST",  # Same as self.role
                }
            )

    def test_role_different_company(self):
        """Verify that roles can be created in different companies."""
        company2 = self.env["res.company"].create(
            {
                "name": "Test Company 2",
            }
        )
        # Note: Same code across companies would fail because res.groups has
        # unique constraint on (category_id, name), and all role groups share
        # the same category. Using different code.
        role2 = self.env["res.role"].create(
            {
                "name": "Role Different Company",
                "code": "TST2",
                "company_id": company2.id,
            }
        )
        self.assertEqual(role2.company_id, company2)

    def test_role_active_field(self):
        """Verify that roles have active field and can be archived."""
        self.assertTrue(self.role.active)
        self.role.active = False
        self.assertFalse(self.role.active)

    def test_role_default_company(self):
        """Verify that default company is set correctly."""
        role = self.env["res.role"].create(
            {
                "name": "Default Company Role",
                "code": "DFCMP",
            }
        )
        self.assertEqual(role.company_id, self.env.user.company_id)

    def test_role_export_xls(self):
        """Verify export_xls returns correct report action."""
        result = self.role.export_xls()
        self.assertEqual(result["type"], "ir.actions.report")
        self.assertEqual(result["report_type"], "xlsx")
        self.assertEqual(result["report_name"], "role_policy.export_xls")

    def test_role_import_policy(self):
        """Verify import_policy returns correct action."""
        result = self.role.import_policy()
        self.assertEqual(result["type"], "ir.actions.act_window")
        self.assertEqual(result["res_model"], "role.policy.import")
        self.assertEqual(result["target"], "new")

    def test_role_group_category(self):
        """Verify that role group is created with correct category."""
        categ = self.env.ref("role_policy.ir_module_category_role")
        self.assertEqual(self.role.group_id.category_id, categ)
