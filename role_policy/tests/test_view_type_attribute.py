# Copyright 2024 Electronic Cats
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import unittest.mock

from lxml import etree
from odoo.tests.common import tagged
from odoo.tools.misc import mute_logger

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
        with mute_logger("odoo.sql_db"):
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
        if not list_view:
            self.skipTest("No list view for res.partner in this environment.")
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


@tagged("post_install", "-at_install")
class TestViewTypeAttributeApplication(RolePolicyTestCommon):
    """Tests that view type attributes actually modify the rendered XML root tag.

    Patches ``config.get("test_enable")`` so the real ``_get_rules`` runs.
    """

    VTA_CONFIG = "odoo.addons.role_policy.models.view_type_attribute.config"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_view = (
            cls.env["ir.ui.view"]
            .with_context(role_policy_init=True)
            .create(
                {
                    "name": "test.partner.vta",
                    "model": "res.partner",
                    "type": "form",
                    "arch": '<form><field name="name"/></form>',
                }
            )
        )

    def _apply_vta_rules(self):
        """Call _apply_view_type_attribute_rules with config patched.

        Uses env(user=test_user, su=True) so _get_rules sees the
        test user's roles while bypassing ACL checks.
        """
        su_env = self.env(user=self.test_user, su=True)
        view = self.env["ir.ui.view"].with_env(su_env).browse(self.test_view.id)
        arch_str = etree.tostring(etree.fromstring(view.arch), encoding="unicode")
        with unittest.mock.patch(self.VTA_CONFIG) as mock_config:
            mock_config.get.return_value = False
            result = view._apply_view_type_attribute_rules(arch_str)
        return etree.fromstring(result)

    def test_create_false_attribute_on_form_root(self):
        """Verify create='false' appears on the <form> root element."""
        self.env["view.type.attribute"].create(
            {
                "role_id": self.role.id,
                "view_id": self.test_view.id,
                "attrib": "create",
                "attrib_val": "false",
            }
        )
        arch_node = self._apply_vta_rules()
        self.assertEqual(
            arch_node.get("create"),
            "false",
            "<form> should have create='false' after VTA rule",
        )

    def test_edit_false_attribute_on_form_root(self):
        """Verify edit='false' appears on the <form> root element."""
        self.env["view.type.attribute"].create(
            {
                "role_id": self.role.id,
                "view_id": self.test_view.id,
                "attrib": "edit",
                "attrib_val": "false",
            }
        )
        arch_node = self._apply_vta_rules()
        self.assertEqual(
            arch_node.get("edit"),
            "false",
            "<form> should have edit='false'",
        )

    def test_delete_false_attribute_on_form_root(self):
        """Verify delete='false' appears on the <form> root element."""
        self.env["view.type.attribute"].create(
            {
                "role_id": self.role.id,
                "view_id": self.test_view.id,
                "attrib": "delete",
                "attrib_val": "false",
            }
        )
        arch_node = self._apply_vta_rules()
        self.assertEqual(
            arch_node.get("delete"),
            "false",
            "<form> should have delete='false'",
        )

    def test_multiple_attributes_on_same_view(self):
        """Verify multiple VTA rules stack on the same view."""
        for attrib in ("create", "edit", "delete"):
            self.env["view.type.attribute"].create(
                {
                    "role_id": self.role.id,
                    "view_id": self.test_view.id,
                    "attrib": attrib,
                    "attrib_val": "false",
                }
            )
        arch_node = self._apply_vta_rules()
        for attrib in ("create", "edit", "delete"):
            self.assertEqual(
                arch_node.get(attrib),
                "false",
                f"<form> should have {attrib}='false'",
            )

    def test_no_rule_leaves_form_untouched(self):
        """Verify form root has no extra attributes when no rules exist."""
        arch_node = self._apply_vta_rules()
        self.assertIsNone(
            arch_node.get("create"),
            "<form> should not have create attribute without rule",
        )
