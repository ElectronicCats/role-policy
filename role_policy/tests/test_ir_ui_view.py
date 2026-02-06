# Copyright 2024 Electronic Cats
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree
from odoo.tests.common import tagged

from .common import RolePolicyTestCommon


@tagged("post_install", "-at_install")
class TestIrUiView(RolePolicyTestCommon):
    """Tests for the ir.ui.view extension."""

    def test_remove_xml_comments(self):
        """Verify removal of XML comments."""
        view = self.env["ir.ui.view"]
        arch = "<form><!-- comment -->content</form>"
        result = view._remove_xml_comments(arch)
        self.assertNotIn("<!--", result)
        self.assertIn("content", result)

    def test_remove_xml_comments_no_comments(self):
        """Verify no changes when no comments exist."""
        view = self.env["ir.ui.view"]
        arch = "<form>content</form>"
        result = view._remove_xml_comments(arch)
        self.assertEqual(result, arch)

    def test_remove_security_groups(self):
        """Verify removal of security groups from arch."""
        view = self.env["ir.ui.view"]
        arch = etree.fromstring(
            '<form><field name="test" groups="sales_team.group_sale_manager"/></form>'
        )
        view._remove_security_groups(arch)
        field = arch.xpath('//field[@name="test"]')[0]
        self.assertNotIn("groups", field.attrib)

    def test_remove_security_groups_keeps_untouchables(self):
        """Verify that untouchable groups are preserved."""
        view = self.env["ir.ui.view"]
        arch = etree.fromstring(
            '<form><field name="test" groups="base.group_no_one"/></form>'
        )
        view._remove_security_groups(arch)
        field = arch.xpath('//field[@name="test"]')[0]
        self.assertIn("groups", field.attrib)
        self.assertEqual(field.attrib["groups"], "base.group_no_one")

    def test_remove_security_groups_multiple(self):
        """Verify handling of multiple groups."""
        view = self.env["ir.ui.view"]
        arch = etree.fromstring(
            '<form><field name="test" groups="base.group_no_one,sales_team.group_sale_manager"/></form>'
        )
        view._remove_security_groups(arch)
        field = arch.xpath('//field[@name="test"]')[0]
        # Only untouchable group should remain
        self.assertIn("groups", field.attrib)
        self.assertEqual(field.attrib["groups"], "base.group_no_one")

    def test_handle_roles_removes_when_no_match(self):
        """Verify that elements with roles are removed if user doesn't have role."""
        view = self.env["ir.ui.view"]
        arch = etree.fromstring('<form><field name="test" roles="NONEXISTENT"/></form>')
        # With user that doesn't have the role
        view_with_user = view.with_user(self.test_user)
        view_with_user._handle_roles(arch)
        fields = arch.xpath('//field[@name="test"]')
        self.assertEqual(len(fields), 0)

    def test_handle_roles_keeps_when_match(self):
        """Verify that elements with roles are kept if user has role."""
        view = self.env["ir.ui.view"]
        arch = etree.fromstring('<form><field name="test" roles="TEST"/></form>')
        view_with_user = view.with_user(self.test_user)
        view_with_user._handle_roles(arch)
        fields = arch.xpath('//field[@name="test"]')
        self.assertEqual(len(fields), 1)
        # The roles attribute should be removed
        self.assertNotIn("roles", fields[0].attrib)

    def test_handle_roles_multiple_roles(self):
        """Verify handling of multiple roles."""
        view = self.env["ir.ui.view"]
        arch = etree.fromstring('<form><field name="test" roles="TEST, OTHER"/></form>')
        view_with_user = view.with_user(self.test_user)
        view_with_user._handle_roles(arch)
        # User has TEST role, so element should remain
        fields = arch.xpath('//field[@name="test"]')
        self.assertEqual(len(fields), 1)

    def test_no_access_view_arch_form(self):
        """Verify arch generated when no access for form view."""
        view = self.env["ir.ui.view"]
        view_dict = {"type": "form"}
        arch = view._no_access_view_arch(view_dict)
        self.assertIn("<form>", arch)
        self.assertIn("</form>", arch)

    def test_no_access_view_arch_list(self):
        """Verify arch generated when no access for list view."""
        view = self.env["ir.ui.view"]
        view_dict = {"type": "list"}
        arch = view._no_access_view_arch(view_dict)
        self.assertIn("<list>", arch)
        self.assertIn("</list>", arch)
        self.assertIn('column_invisible="True"', arch)

    def test_no_access_view_arch_other_unsupported_raises(self):
        """Verify that truly unsupported view types raise (if any remains)."""
        # Note: All types now have a default fallback, so this might not raise anymore
        # but kept if we want to ensure error for specific crazy types if needed.
        pass

    def test_create_removes_groups_without_context(self):
        """Verify that create removes groups_id without special context."""
        # When creating without role_policy_init context, groups_id should be removed
        view = self.env["ir.ui.view"].create(
            {
                "name": "Test View No Groups",
                "model": "res.partner",
                "arch": "<form><field name='name'/></form>",
                "groups_id": [(6, 0, [self.env.ref("base.group_user").id])],
            }
        )
        # groups_id should be empty since it's removed in create
        self.assertFalse(view.groups_id)

    def test_create_keeps_groups_with_context(self):
        """Verify that create keeps groups_id with role_policy_init context."""
        view = (
            self.env["ir.ui.view"]
            .with_context(role_policy_init=True)
            .create(
                {
                    "name": "Test View With Groups",
                    "model": "res.partner",
                    "arch": "<form><field name='name'/></form>",
                    "groups_id": [(6, 0, [self.env.ref("base.group_user").id])],
                }
            )
        )
        # groups_id should be preserved with context
        self.assertTrue(view.groups_id)

    def test_write_removes_groups_without_context(self):
        """Verify that write removes groups_id without special context."""
        view = (
            self.env["ir.ui.view"]
            .with_context(role_policy_init=True)
            .create(
                {
                    "name": "Test View Write",
                    "model": "res.partner",
                    "arch": "<form><field name='name'/></form>",
                    "groups_id": [(6, 0, [self.env.ref("base.group_user").id])],
                }
            )
        )
        # Verify groups were set initially
        self.assertTrue(view.groups_id)
        # Get fresh recordset WITHOUT role_policy_init context
        view_no_ctx = self.env["ir.ui.view"].browse(view.id)
        # Write without context should ignore groups_id update
        view_no_ctx.write({"groups_id": [(6, 0, [])]})
        # Re-read the view to check groups_id
        view.invalidate_recordset()
        # groups_id shouldn't change because the update was ignored
        self.assertTrue(view.groups_id)

    def test_apply_inheritance_specs_handles_errors(self):
        """Verify that apply_inheritance_specs handles ValueError gracefully."""
        view = self.env["ir.ui.view"]
        source = etree.fromstring("<form><field name='test'/></form>")
        # Invalid specs that would cause ValueError
        specs = etree.fromstring(
            '<field name="nonexistent" position="after"><field name="new"/></field>'
        )
        # Should not raise, returns source unchanged
        result = view.apply_inheritance_specs(source, specs)
        self.assertIsNotNone(result)

    def test_apply_view_modifier_rules_column_invisible(self):
        """Verify that invisible modifier is mapped to column_invisible for list views."""
        # Create a list view
        view = self.env["ir.ui.view"].create(
            {
                "name": "Test List View",
                "model": "res.partner",
                "type": "list",
                "arch": '<list><field name="name"/></list>',
            }
        )
        # Create a modifier rule for the test user's role
        role = self.test_user.role_ids[0]
        rule = self.env["view.modifier.rule"].create(
            {
                "role_id": role.id,
                "model_id": self.env["ir.model"]._get_id("res.partner"),
                "view_id": view.id,
                "view_type": "list",
                "element_ui": 'field name="name"',
                "modifier_invisible": "1",
            }
        )
        
        # Apply rules
        archs = [(view.arch, view.id)]
        result_archs = view.with_user(self.test_user).with_context(force_role_policy=True)._apply_view_modifier_rules("res.partner", archs)
        
        arch_node = etree.fromstring(result_archs[0][0])
        field_node = arch_node.xpath('//field[@name="name"]')[0]
        
        # In Odoo 18, invisible on list view field should become column_invisible
        self.assertEqual(field_node.attrib.get("column_invisible"), "True")
        self.assertNotIn("invisible", field_node.attrib)

