# Copyright 2024 Electronic Cats
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests.common import tagged

from .common import RolePolicyTestCommon


@tagged("post_install", "-at_install")
class TestViewModelOperation(RolePolicyTestCommon):
    """Tests for the view.model.operation model."""

    def test_operation_create(self):
        """Verify operation can be created."""
        operation = self.env["view.model.operation"].create(
            {
                "role_id": self.role.id,
                "model": "res.partner",
                "operation": "create",
                "disable": True,
            }
        )
        self.assertTrue(operation.disable)
        self.assertEqual(operation.operation, "create")

    def test_operation_default_model(self):
        """Verify operation with 'default' model."""
        operation = self.env["view.model.operation"].create(
            {
                "role_id": self.role.id,
                "model": "default",
                "operation": "delete",
                "disable": True,
            }
        )
        self.assertEqual(operation.model, "default")

    def test_operation_compute_sort_default(self):
        """Verify sort is '0' for 'default' model."""
        operation = self.env["view.model.operation"].create(
            {
                "role_id": self.role.id,
                "model": "default",
                "operation": "export",
                "disable": True,
            }
        )
        self.assertEqual(operation.sort, "0")

    def test_operation_compute_sort_model(self):
        """Verify sort equals model name for specific models."""
        operation = self.env["view.model.operation"].create(
            {
                "role_id": self.role.id,
                "model": "res.partner",
                "operation": "import",
                "disable": True,
            }
        )
        self.assertEqual(operation.sort, "res.partner")

    def test_operation_onchange_model_invalid(self):
        """Verify onchange raises error for invalid model."""
        operation = self.env["view.model.operation"].new(
            {
                "role_id": self.role.id,
                "model": "invalid.model.that.does.not.exist",
                "operation": "create",
            }
        )
        with self.assertRaises(UserError):
            operation._onchange_model()

    def test_operation_onchange_model_valid(self):
        """Verify onchange passes for valid model."""
        operation = self.env["view.model.operation"].new(
            {
                "role_id": self.role.id,
                "model": "res.partner",
                "operation": "create",
            }
        )
        # Should not raise
        operation._onchange_model()

    def test_operation_selection(self):
        """Verify available operations."""
        operation = self.env["view.model.operation"]
        selections = operation._selection_operation()
        operation_keys = [s[0] for s in selections]
        self.assertIn("create", operation_keys)
        self.assertIn("edit", operation_keys)
        self.assertIn("delete", operation_keys)
        self.assertIn("duplicate", operation_keys)
        self.assertIn("export", operation_keys)
        self.assertIn("import", operation_keys)
        self.assertIn("archive", operation_keys)

    def test_operations_dict(self):
        """Verify _operations_dict returns expected structure."""
        operation = self.env["view.model.operation"]
        ops_dict = operation._operations_dict()
        self.assertIn("create", ops_dict)
        self.assertIn("label", ops_dict["create"])
        self.assertIn("view_types", ops_dict["create"])

    def test_operations_dict_export_attribute(self):
        """Verify export operation has view_type_attribute."""
        operation = self.env["view.model.operation"]
        ops_dict = operation._operations_dict()
        self.assertIn("export", ops_dict)
        self.assertEqual(ops_dict["export"]["view_type_attribute"], "export_xlsx")

    def test_operation_unique_constraint(self):
        """Verify unique constraint on role/model/operation."""
        self.env["view.model.operation"].create(
            {
                "role_id": self.role.id,
                "model": "res.partner",
                "operation": "create",
                "disable": True,
            }
        )
        with self.assertRaises(Exception):  # noqa: B017
            self.env["view.model.operation"].create(
                {
                    "role_id": self.role.id,
                    "model": "res.partner",
                    "operation": "create",
                    "disable": False,
                }
            )

    def test_operation_priority_default(self):
        """Verify default priority value."""
        operation = self.env["view.model.operation"].create(
            {
                "role_id": self.role.id,
                "model": "res.partner",
                "operation": "edit",
                "disable": True,
            }
        )
        self.assertEqual(operation.priority, 16)

    def test_operation_active_field(self):
        """Verify active field works."""
        operation = self.env["view.model.operation"].create(
            {
                "role_id": self.role.id,
                "model": "res.partner",
                "operation": "duplicate",
                "disable": True,
            }
        )
        self.assertTrue(operation.active)
        operation.active = False
        self.assertFalse(operation.active)

    def test_operation_company_related(self):
        """Verify company_id is related from role."""
        operation = self.env["view.model.operation"].create(
            {
                "role_id": self.role.id,
                "model": "res.partner",
                "operation": "archive",
                "disable": True,
            }
        )
        self.assertEqual(operation.company_id, self.role.company_id)

    def test_rule_signature_fields(self):
        """Verify _rule_signature_fields returns expected fields."""
        operation = self.env["view.model.operation"]
        signature_fields = operation._rule_signature_fields()
        self.assertIn("model", signature_fields)
        self.assertIn("operation", signature_fields)
