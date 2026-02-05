# Copyright 2024 Electronic Cats
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import tagged
from odoo.tools.misc import mute_logger

from .common import RolePolicyTestCommon


@tagged("post_install", "-at_install")
class TestResRoleAcl(RolePolicyTestCommon):
    """Tests for the res.role.acl model."""

    def test_acl_create_creates_group_and_access(self):
        """Verify that creating an ACL creates a group and access record."""
        acl = self.env["res.role.acl"].create(
            {
                "role_id": self.role.id,
                "model_id": self.partner_model.id,
                "perm_read": True,
                "perm_write": True,
            }
        )
        self.assertTrue(acl.group_id, "ACL should have an associated group")
        self.assertTrue(acl.access_id, "ACL should have an associated access")
        self.assertIn("role_acl_res_partner_ru", acl.group_id.name)
        self.assertIn(acl.group_id, self.role.group_id.implied_ids)

    def test_acl_create_name_format(self):
        """Verify that ACL name is formatted correctly."""
        acl = self.env["res.role.acl"].create(
            {
                "role_id": self.role.id,
                "model_id": self.partner_model.id,
                "perm_read": True,
            }
        )
        self.assertIn(self.role.code, acl.name)
        self.assertIn("role_acl_res_partner_r", acl.name)

    def test_acl_write_updates_group(self):
        """Verify that modifying permissions updates the group."""
        acl = self.env["res.role.acl"].create(
            {
                "role_id": self.role.id,
                "model_id": self.partner_model.id,
                "perm_read": True,
            }
        )
        old_group = acl.group_id
        acl.write({"perm_write": True})
        self.assertNotEqual(acl.group_id, old_group)
        self.assertIn("ru", acl.group_id.name)

    def test_acl_unlink_removes_from_implied(self):
        """Verify that deleting an ACL removes group from implied_ids."""
        acl = self.env["res.role.acl"].create(
            {
                "role_id": self.role.id,
                "model_id": self.partner_model.id,
                "perm_read": True,
            }
        )
        acl_group = acl.group_id
        self.assertIn(acl_group, self.role.group_id.implied_ids)
        acl.unlink()
        self.assertNotIn(acl_group, self.role.group_id.implied_ids)

    def test_acl_compute_crud_create_only(self):
        """Verify _compute_crud for create permission only."""
        acl = self.env["res.role.acl"].create(
            {
                "role_id": self.role.id,
                "model_id": self.partner_model.id,
                "perm_create": True,
            }
        )
        crud = acl._compute_crud({})
        self.assertEqual(crud, "c")

    def test_acl_compute_crud_read_only(self):
        """Verify _compute_crud for read permission only."""
        acl = self.env["res.role.acl"].create(
            {
                "role_id": self.role.id,
                "model_id": self.partner_model.id,
                "perm_read": True,
            }
        )
        crud = acl._compute_crud({})
        self.assertEqual(crud, "r")

    def test_acl_compute_crud_full(self):
        """Verify _compute_crud for all permissions."""
        acl = self.env["res.role.acl"].create(
            {
                "role_id": self.role.id,
                "model_id": self.partner_model.id,
                "perm_create": True,
                "perm_read": True,
                "perm_write": True,
                "perm_unlink": True,
            }
        )
        crud = acl._compute_crud({})
        self.assertEqual(crud, "crud")

    def test_acl_compute_crud_from_vals(self):
        """Verify _compute_crud uses vals over existing values."""
        acl = self.env["res.role.acl"].create(
            {
                "role_id": self.role.id,
                "model_id": self.partner_model.id,
                "perm_read": True,
            }
        )
        crud = acl._compute_crud({"perm_write": True})
        self.assertEqual(crud, "ru")

    def test_acl_toggle_active_false(self):
        """Verify that deactivating ACL removes from implied_ids."""
        acl = self.env["res.role.acl"].create(
            {
                "role_id": self.role.id,
                "model_id": self.partner_model.id,
                "perm_read": True,
            }
        )
        self.assertIn(acl.group_id, self.role.group_id.implied_ids)

        acl.write({"active": False})
        self.assertNotIn(acl.group_id, self.role.group_id.implied_ids)

    def test_acl_toggle_active_true(self):
        """Verify that reactivating ACL adds back to implied_ids."""
        acl = self.env["res.role.acl"].create(
            {
                "role_id": self.role.id,
                "model_id": self.partner_model.id,
                "perm_read": True,
            }
        )
        acl.write({"active": False})
        acl.write({"active": True})
        self.assertIn(acl.group_id, self.role.group_id.implied_ids)

    def test_acl_crud_not_null_constraint(self):
        """Verify constraint that at least one permission must be set."""
        with mute_logger("odoo.sql_db"):
            with self.assertRaises(Exception):  # noqa: B017
                self.env["res.role.acl"].create(
                    {
                        "role_id": self.role.id,
                        "model_id": self.partner_model.id,
                        "perm_create": False,
                        "perm_read": False,
                        "perm_write": False,
                        "perm_unlink": False,
                    }
                )

    def test_acl_model_role_unique_constraint(self):
        """Verify unique constraint on model/role combination."""
        self.env["res.role.acl"].create(
            {
                "role_id": self.role.id,
                "model_id": self.partner_model.id,
                "perm_read": True,
            }
        )
        with mute_logger("odoo.sql_db"):
            with self.assertRaises(Exception):  # noqa: B017
                self.env["res.role.acl"].create(
                    {
                        "role_id": self.role.id,
                        "model_id": self.partner_model.id,
                        "perm_write": True,
                    }
                )

    def test_acl_access_permissions(self):
        """Verify that access record has correct permissions."""
        acl = self.env["res.role.acl"].create(
            {
                "role_id": self.role.id,
                "model_id": self.partner_model.id,
                "perm_create": True,
                "perm_read": True,
                "perm_write": False,
                "perm_unlink": True,
            }
        )
        self.assertTrue(acl.access_id.perm_create)
        self.assertTrue(acl.access_id.perm_read)
        self.assertFalse(acl.access_id.perm_write)
        self.assertTrue(acl.access_id.perm_unlink)

    def test_acl_group_reuse(self):
        """Verify that groups are reused for same model/permissions."""
        # Create first role with ACL
        role1 = self.env["res.role"].create(
            {
                "name": "Role 1",
                "code": "ROL1",
            }
        )
        acl1 = self.env["res.role.acl"].create(
            {
                "role_id": role1.id,
                "model_id": self.partner_model.id,
                "perm_read": True,
            }
        )

        # Create second role with same ACL
        role2 = self.env["res.role"].create(
            {
                "name": "Role 2",
                "code": "ROL2",
            }
        )
        acl2 = self.env["res.role.acl"].create(
            {
                "role_id": role2.id,
                "model_id": self.partner_model.id,
                "perm_read": True,
            }
        )

        # Both should use the same underlying group
        self.assertEqual(acl1.group_id, acl2.group_id)

    def test_acl_company_in_group_name(self):
        """Verify that company ID is included in group name when set."""
        company = self.env["res.company"].create({"name": "Test Company ACL"})
        role = self.env["res.role"].create(
            {
                "name": "Company Role",
                "code": "CMPR",
                "company_id": company.id,
            }
        )
        acl = self.env["res.role.acl"].create(
            {
                "role_id": role.id,
                "model_id": self.partner_model.id,
                "perm_read": True,
            }
        )
        self.assertIn(str(company.id), acl.group_id.name)

    def test_acl_unlink_preserves_shared_groups(self):
        """Verify that unlinking ACL preserves group for other users with same ACL."""
        # Create two roles with same ACL
        role2 = self.env["res.role"].create(
            {
                "name": "Role 2",
                "code": "ROL2",
            }
        )
        acl1 = self.env["res.role.acl"].create(
            {
                "role_id": self.role.id,
                "model_id": self.partner_model.id,
                "perm_read": True,
            }
        )
        acl2 = self.env["res.role.acl"].create(
            {
                "role_id": role2.id,
                "model_id": self.partner_model.id,
                "perm_read": True,
            }
        )
        shared_group = acl1.group_id
        self.assertEqual(shared_group, acl2.group_id)

        # Create user with both roles
        self.env["res.users"].create(
            {
                "name": "Multi Role User",
                "login": "multi_role_user",
                "role_ids": [(6, 0, [self.role.id, role2.id])],
            }
        )

        # Delete first ACL - user should still have group via role2
        acl1.unlink()
        self.assertIn(shared_group, role2.group_id.implied_ids)
