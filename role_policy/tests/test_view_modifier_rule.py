# Copyright 2024 Electronic Cats
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests.common import tagged
from odoo.tools.misc import mute_logger

from .common import RolePolicyTestCommon


@tagged("post_install", "-at_install")
class TestViewModifierRule(RolePolicyTestCommon):
    """Tests for the view.modifier.rule model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create ACL for the role so we can create modifier rules
        cls.acl = cls.env["res.role.acl"].create(
            {
                "role_id": cls.role.id,
                "model_id": cls.partner_model.id,
                "perm_read": True,
            }
        )

    def test_rule_element_resolution_simple_field(self):
        """Verify resolution of simple field element_ui."""
        rule = self.env["view.modifier.rule"].create(
            {
                "role_id": self.role.id,
                "model_id": self.partner_model.id,
                "view_type": "form",
                "element_ui": 'field name="name"',
                "modifier_readonly": "1",
            }
        )
        self.assertEqual(rule.element, 'field name="name"')

    def test_rule_element_resolution_button(self):
        """Verify resolution of button element_ui."""
        rule = self.env["view.modifier.rule"].create(
            {
                "role_id": self.role.id,
                "model_id": self.partner_model.id,
                "view_type": "form",
                "element_ui": 'button name="test_button"',
                "modifier_invisible": "1",
            }
        )
        self.assertEqual(rule.element, 'button name="test_button"')

    def test_rule_element_resolution_xpath(self):
        """Verify resolution of element_ui with xpath."""
        rule = self.env["view.modifier.rule"].create(
            {
                "role_id": self.role.id,
                "model_id": self.partner_model.id,
                "view_type": "form",
                "element_ui": "xpath expr=\"//field[@name='name']\"",
                "modifier_invisible": "1",
            }
        )
        self.assertIn("xpath", rule.element)

    def test_rule_check_view_consistency(self):
        """Verify constraint that view_type must match view_id.type."""
        with self.assertRaises(UserError):
            self.env["view.modifier.rule"].create(
                {
                    "role_id": self.role.id,
                    "model_id": self.partner_model.id,
                    "view_id": self.partner_form_view.id,
                    "view_type": "list",  # Inconsistent with form view
                    "element_ui": 'field name="name"',
                    "modifier_readonly": "1",
                }
            )

    def test_rule_remove_requires_view(self):
        """Verify that remove=True requires view_id."""
        with self.assertRaises(UserError):
            self.env["view.modifier.rule"].create(
                {
                    "role_id": self.role.id,
                    "model_id": self.partner_model.id,
                    "view_type": "form",
                    "element_ui": 'field name="name"',
                    "remove": True,
                }
            )

    def test_rule_remove_with_view(self):
        """Verify that remove=True works with view_id."""
        rule = self.env["view.modifier.rule"].create(
            {
                "role_id": self.role.id,
                "model_id": self.partner_model.id,
                "view_id": self.partner_form_view.id,
                "view_type": "form",
                "element_ui": 'field name="name"',
                "remove": True,
            }
        )
        self.assertTrue(rule.remove)

    def test_rule_unique_constraint(self):
        """Verify unique constraint on element per role/model/view."""
        self.env["view.modifier.rule"].create(
            {
                "role_id": self.role.id,
                "model_id": self.partner_model.id,
                "view_type": "form",
                "element_ui": 'field name="email"',
                "modifier_readonly": "1",
            }
        )
        with mute_logger("odoo.sql_db"):
            with self.assertRaises(Exception):  # noqa: B017
                self.env["view.modifier.rule"].create(
                    {
                        "role_id": self.role.id,
                        "model_id": self.partner_model.id,
                        "view_type": "form",
                        "element_ui": 'field name="email"',
                        "modifier_invisible": "1",
                    }
                )

    def test_rule_onchange_view_id(self):
        """Verify that onchange sets view_type from view_id."""
        rule = self.env["view.modifier.rule"].new(
            {
                "role_id": self.role.id,
                "model_id": self.partner_model.id,
                "view_id": self.partner_form_view.id,
            }
        )
        rule._onchange_view_id()
        self.assertEqual(rule.view_type, "form")

    def test_rule_onchange_view_id_clears_remove(self):
        """Verify that clearing view_id also clears remove."""
        rule = self.env["view.modifier.rule"].new(
            {
                "role_id": self.role.id,
                "model_id": self.partner_model.id,
                "view_id": self.partner_form_view.id,
                "remove": True,
            }
        )
        rule.view_id = False
        rule._onchange_view_id()
        self.assertFalse(rule.remove)

    def test_rule_selection_view_type(self):
        """Verify available view types."""
        rule = self.env["view.modifier.rule"]
        view_types = rule._selection_view_type()
        view_type_keys = [vt[0] for vt in view_types]
        self.assertIn("form", view_type_keys)
        self.assertIn("list", view_type_keys)
        self.assertIn("kanban", view_type_keys)
        self.assertIn("search", view_type_keys)

    def test_rule_modifier_readonly(self):
        """Verify modifier_readonly can be set."""
        rule = self.env["view.modifier.rule"].create(
            {
                "role_id": self.role.id,
                "model_id": self.partner_model.id,
                "view_type": "form",
                "element_ui": 'field name="phone"',
                "modifier_readonly": "1",
            }
        )
        self.assertEqual(rule.modifier_readonly, "1")

    def test_rule_modifier_invisible(self):
        """Verify modifier_invisible can be set."""
        rule = self.env["view.modifier.rule"].create(
            {
                "role_id": self.role.id,
                "model_id": self.partner_model.id,
                "view_type": "form",
                "element_ui": 'field name="mobile"',
                "modifier_invisible": "1",
            }
        )
        self.assertEqual(rule.modifier_invisible, "1")

    def test_rule_modifier_required(self):
        """Verify modifier_required can be set."""
        rule = self.env["view.modifier.rule"].create(
            {
                "role_id": self.role.id,
                "model_id": self.partner_model.id,
                "view_type": "form",
                "element_ui": 'field name="street"',
                "modifier_required": "1",
            }
        )
        self.assertEqual(rule.modifier_required, "1")

    def test_rule_modifier_domain(self):
        """Verify modifier can be a domain expression."""
        rule = self.env["view.modifier.rule"].create(
            {
                "role_id": self.role.id,
                "model_id": self.partner_model.id,
                "view_type": "form",
                "element_ui": 'field name="city"',
                "modifier_invisible": "[('country_id', '=', False)]",
            }
        )
        self.assertEqual(rule.modifier_invisible, "[('country_id', '=', False)]")

    def test_rule_priority_default(self):
        """Verify default priority value."""
        rule = self.env["view.modifier.rule"].create(
            {
                "role_id": self.role.id,
                "model_id": self.partner_model.id,
                "view_type": "form",
                "element_ui": 'field name="zip"',
                "modifier_readonly": "1",
            }
        )
        self.assertEqual(rule.priority, 16)

    def test_rule_sequence_default(self):
        """Verify default sequence value."""
        rule = self.env["view.modifier.rule"].create(
            {
                "role_id": self.role.id,
                "model_id": self.partner_model.id,
                "view_type": "form",
                "element_ui": 'field name="state_id"',
                "modifier_readonly": "1",
            }
        )
        self.assertEqual(rule.sequence, 16)

    def test_rule_active_field(self):
        """Verify active field works."""
        rule = self.env["view.modifier.rule"].create(
            {
                "role_id": self.role.id,
                "model_id": self.partner_model.id,
                "view_type": "form",
                "element_ui": 'field name="country_id"',
                "modifier_readonly": "1",
            }
        )
        self.assertTrue(rule.active)
        rule.active = False
        self.assertFalse(rule.active)

    def test_rule_company_related(self):
        """Verify company_id is related from role."""
        rule = self.env["view.modifier.rule"].create(
            {
                "role_id": self.role.id,
                "model_id": self.partner_model.id,
                "view_type": "form",
                "element_ui": 'field name="website"',
                "modifier_readonly": "1",
            }
        )
        self.assertEqual(rule.company_id, self.role.company_id)

    def test_rule_signature_fields(self):
        """Verify _rule_signature_fields returns expected fields."""
        rule = self.env["view.modifier.rule"]
        signature_fields = rule._rule_signature_fields()
        self.assertIn("element", signature_fields)
        self.assertIn("view_id", signature_fields)
        self.assertIn("view_type", signature_fields)
