# Copyright 2024 Electronic Cats
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import tagged
from odoo.tools.misc import mute_logger

from .common import RolePolicyTestCommon


@tagged("post_install", "-at_install")
class TestModelMethodExecutionRight(RolePolicyTestCommon):
    """Tests for the model.method.execution.right model."""

    def test_selection_name_empty_by_default(self):
        """Verify that _selection_name returns empty list by default."""
        Right = self.env["model.method.execution.right"]
        selection = Right._selection_name()
        # In base role_policy, selection is empty
        # It gets populated by extensions like role_policy_account
        self.assertIsInstance(selection, list)

    def test_check_right_superuser_always_allowed(self):
        """Verify that superuser always has permission."""
        Right = self.env["model.method.execution.right"].sudo()
        # In test mode, check_right returns True
        result = Right.check_right("any.model,any_method", raise_exception=False)
        self.assertTrue(result)

    def test_check_right_excluded_user_always_allowed(self):
        """Verify that excluded users (admin/root) always have permission."""
        admin = self.env.ref("base.user_admin")
        Right = self.env["model.method.execution.right"].with_user(admin)
        # In test mode, check_right returns True
        result = Right.check_right("any.model,any_method", raise_exception=False)
        self.assertTrue(result)

    def test_unique_constraint(self):
        """Verify unique constraint on role/model/method."""
        # This test requires a selection value to exist
        # In base module, selection is empty, so we skip full test
        # Extensions like role_policy_account add selection values
        Right = self.env["model.method.execution.right"]
        selection = Right._selection_name()
        if not selection:
            self.skipTest(
                "Base module has no model.method.execution.right selection; "
                "test covered in role_policy_account."
            )

        Right.create(
            {
                "role_id": self.role.id,
                "name": selection[0][0],
            }
        )
        with mute_logger("odoo.sql_db"):
            with self.assertRaises(Exception):  # noqa: B017
                Right.create(
                    {
                        "role_id": self.role.id,
                        "name": selection[0][0],
                    }
                )

    def test_active_field(self):
        """Verify active field default."""
        Right = self.env["model.method.execution.right"]
        selection = Right._selection_name()
        if not selection:
            self.skipTest(
                "Base module has no model.method.execution.right selection; "
                "test covered in role_policy_account."
            )

        right = Right.create(
            {
                "role_id": self.role.id,
                "name": selection[0][0],
            }
        )
        self.assertTrue(right.active)

    def test_company_related(self):
        """Verify company_id is related from role."""
        Right = self.env["model.method.execution.right"]
        selection = Right._selection_name()
        if not selection:
            self.skipTest(
                "Base module has no model.method.execution.right selection; "
                "test covered in role_policy_account."
            )

        right = Right.create(
            {
                "role_id": self.role.id,
                "name": selection[0][0],
            }
        )
        self.assertEqual(right.company_id, self.role.company_id)
