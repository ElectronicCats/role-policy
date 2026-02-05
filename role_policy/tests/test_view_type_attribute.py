# Copyright 2024 Electronic Cats
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import tagged

from .common import RolePolicyTestCommon


@tagged("post_install", "-at_install")
class TestViewTypeAttribute(RolePolicyTestCommon):
    """Tests for the view.type.attribute model."""

    def test_attribute_create(self):
        """Verify attribute can be created."""
        attribute = self.env["view.type.attribute"].create(
            {
                "role_id": self.role.id,
                "view_id": self.partner_form_view.id,
                "attrib": "export_xlsx",
                "attrib_val": "0",
            }
        )
        self.assertEqual(attribute.attrib, "export_xlsx")
        self.assertEqual(attribute.attrib_val, "0")

    def test_attribute_view_type_related(self):
        """Verify view_type is related from view_id."""
        attribute = self.env["view.type.attribute"].create(
            {
                "role_id": self.role.id,
                "view_id": self.partner_form_view.id,
                "attrib": "create",
                "attrib_val": "0",
            }
        )
        self.assertEqual(attribute.view_type, "form")

    def test_attribute_view_xml_id_related(self):
        """Verify view_xml_id is related from view_id."""
        attribute = self.env["view.type.attribute"].create(
            {
                "role_id": self.role.id,
                "view_id": self.partner_form_view.id,
                "attrib": "edit",
                "attrib_val": "0",
            }
        )
        self.assertEqual(attribute.view_xml_id, "base.view_partner_form")

    def test_attribute_unique_constraint(self):
        """Verify unique constraint on role/view/attrib."""
        self.env["view.type.attribute"].create(
            {
                "role_id": self.role.id,
                "view_id": self.partner_form_view.id,
                "attrib": "delete",
                "attrib_val": "0",
            }
        )
        with self.assertRaises(Exception):  # noqa: B017
            self.env["view.type.attribute"].create(
                {
                    "role_id": self.role.id,
                    "view_id": self.partner_form_view.id,
                    "attrib": "delete",
                    "attrib_val": "1",
                }
            )

    def test_attribute_priority_default(self):
        """Verify default priority value."""
        attribute = self.env["view.type.attribute"].create(
            {
                "role_id": self.role.id,
                "view_id": self.partner_form_view.id,
                "attrib": "duplicate",
                "attrib_val": "0",
            }
        )
        self.assertEqual(attribute.priority, 16)

    def test_attribute_sequence_default(self):
        """Verify default sequence value."""
        attribute = self.env["view.type.attribute"].create(
            {
                "role_id": self.role.id,
                "view_id": self.partner_form_view.id,
                "attrib": "import",
                "attrib_val": "0",
            }
        )
        self.assertEqual(attribute.sequence, 16)

    def test_attribute_active_field(self):
        """Verify active field works."""
        attribute = self.env["view.type.attribute"].create(
            {
                "role_id": self.role.id,
                "view_id": self.partner_form_view.id,
                "attrib": "archive",
                "attrib_val": "0",
            }
        )
        self.assertTrue(attribute.active)
        attribute.active = False
        self.assertFalse(attribute.active)

    def test_attribute_company_related(self):
        """Verify company_id is related from role."""
        attribute = self.env["view.type.attribute"].create(
            {
                "role_id": self.role.id,
                "view_id": self.partner_form_view.id,
                "attrib": "sample",
                "attrib_val": "0",
            }
        )
        self.assertEqual(attribute.company_id, self.role.company_id)

    def test_rule_signature_fields(self):
        """Verify _rule_signature_fields returns expected fields."""
        attribute = self.env["view.type.attribute"]
        signature_fields = attribute._rule_signature_fields()
        self.assertIn("view_id", signature_fields)
        self.assertIn("attrib", signature_fields)

    def test_attribute_different_views(self):
        """Verify same attribute can be set on different views."""
        list_view = self.env["ir.ui.view"].search(
            [
                ("model", "=", "res.partner"),
                ("type", "=", "list"),
            ],
            limit=1,
        )
        if list_view:
            attr1 = self.env["view.type.attribute"].create(
                {
                    "role_id": self.role.id,
                    "view_id": self.partner_form_view.id,
                    "attrib": "test_attr",
                    "attrib_val": "form_value",
                }
            )
            attr2 = self.env["view.type.attribute"].create(
                {
                    "role_id": self.role.id,
                    "view_id": list_view.id,
                    "attrib": "test_attr",
                    "attrib_val": "list_value",
                }
            )
            self.assertNotEqual(attr1.view_id, attr2.view_id)
            self.assertEqual(attr1.attrib, attr2.attrib)
