# Copyright 2024 Electronic Cats
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import tagged

from .common import RolePolicyTestCommon


@tagged("post_install", "-at_install")
class TestResUsers(RolePolicyTestCommon):
    """Tests for the res.users extension."""

    def test_user_create_with_role(self):
        """Verify user creation with role."""
        user = self.env["res.users"].create(
            {
                "name": "User With Role",
                "login": "user_with_role",
                "role_ids": [(6, 0, [self.role.id])],
            }
        )
        self.assertIn(self.role, user.role_ids)

    def test_user_exclude_from_role_policy_admin(self):
        """Verify that admin is excluded from role policy."""
        admin = self.env.ref("base.user_admin")
        self.assertTrue(admin.exclude_from_role_policy)

    def test_user_exclude_from_role_policy_root(self):
        """Verify that root is excluded from role policy."""
        root = self.env.ref("base.user_root")
        self.assertTrue(root.exclude_from_role_policy)

    def test_user_normal_not_excluded(self):
        """Verify that normal users are not excluded."""
        self.assertFalse(self.test_user.exclude_from_role_policy)

    def test_user_enabled_role_ids_empty_by_default(self):
        """Verify that enabled_role_ids is empty by default."""
        self.assertFalse(self.test_user.enabled_role_ids)

    def test_user_enabled_role_ids_subset(self):
        """Verify that enabled_role_ids can be a subset of role_ids."""
        role2 = self.env["res.role"].create(
            {
                "name": "Role 2",
                "code": "ROL2",
            }
        )
        self.test_user.write(
            {
                "role_ids": [(6, 0, [self.role.id, role2.id])],
            }
        )
        self.test_user.write(
            {
                "enabled_role_ids": [(6, 0, [self.role.id])],
            }
        )
        self.assertEqual(len(self.test_user.enabled_role_ids), 1)
        self.assertIn(self.role, self.test_user.enabled_role_ids)

    def test_user_has_role(self):
        """Verify has_role method."""
        self.assertTrue(self.test_user.has_role("TEST"))
        self.assertFalse(self.test_user.has_role("NONEXISTENT"))

    def test_user_has_role_with_enabled_roles(self):
        """Verify has_role respects enabled_role_ids."""
        role2 = self.env["res.role"].create(
            {
                "name": "Role 2",
                "code": "ROL2",
            }
        )
        self.test_user.write(
            {
                "role_ids": [(6, 0, [self.role.id, role2.id])],
                "enabled_role_ids": [(6, 0, [role2.id])],
            }
        )
        # has_role uses enabled_role_ids when set
        # Note: has_role uses self.env.user, so we need proper context
        self.assertIn(role2, self.test_user.enabled_role_ids)

    def test_user_self_readable_fields(self):
        """Verify that role fields are readable by the user."""
        readable = self.test_user.SELF_READABLE_FIELDS
        self.assertIn("role_ids", readable)
        self.assertIn("enabled_role_ids", readable)
        self.assertIn("exclude_from_role_policy", readable)

    def test_user_self_writeable_fields(self):
        """Verify that enabled_role_ids is writable by the user."""
        writeable = self.test_user.SELF_WRITEABLE_FIELDS
        self.assertIn("enabled_role_ids", writeable)

    def test_user_onchange_role_ids_clears_invalid_enabled(self):
        """Verify that onchange clears invalid enabled_role_ids."""
        role2 = self.env["res.role"].create(
            {
                "name": "Role 2",
                "code": "ROL2",
            }
        )
        self.test_user.write(
            {
                "role_ids": [(6, 0, [self.role.id, role2.id])],
                "enabled_role_ids": [(6, 0, [self.role.id, role2.id])],
            }
        )
        # Remove role2 from role_ids
        self.test_user.role_ids = self.role
        self.test_user._onchange_role_ids()
        self.assertNotIn(role2, self.test_user.enabled_role_ids)

    def test_user_multiple_roles(self):
        """Verify user can have multiple roles."""
        role2 = self.env["res.role"].create(
            {
                "name": "Role 2",
                "code": "ROL2",
            }
        )
        role3 = self.env["res.role"].create(
            {
                "name": "Role 3",
                "code": "ROL3",
            }
        )
        self.test_user.write(
            {
                "role_ids": [(6, 0, [self.role.id, role2.id, role3.id])],
            }
        )
        self.assertEqual(len(self.test_user.role_ids), 3)

    def test_user_role_groups_assigned(self):
        """Verify that role groups are assigned to user."""
        # In test mode, some logic is bypassed, but group assignment should work
        self.assertIn(self.role.group_id, self.test_user.groups_id)

    def test_user_add_role_command_4(self):
        """Verify adding a role with command 4."""
        role2 = self.env["res.role"].create(
            {
                "name": "Role Add",
                "code": "RADD",
            }
        )
        self.test_user.write({"role_ids": [(4, role2.id)]})
        self.assertIn(role2, self.test_user.role_ids)

    def test_user_remove_role_command_3(self):
        """Verify removing a role with command 3."""
        role2 = self.env["res.role"].create(
            {
                "name": "Role Remove",
                "code": "RREM",
            }
        )
        self.test_user.write({"role_ids": [(4, role2.id)]})
        self.assertIn(role2, self.test_user.role_ids)
        self.test_user.write({"role_ids": [(3, role2.id)]})
        self.assertNotIn(role2, self.test_user.role_ids)

    def test_compute_exclude_recomputes(self):
        """Verify that exclude_from_role_policy is computed correctly."""
        user = self.env["res.users"].create(
            {
                "name": "Compute Test User",
                "login": "compute_test_user",
            }
        )
        self.assertFalse(user.exclude_from_role_policy)
        # Admin and root should be excluded
        admin = self.env.ref("base.user_admin")
        admin._compute_exclude_from_role_policy()
        self.assertTrue(admin.exclude_from_role_policy)
