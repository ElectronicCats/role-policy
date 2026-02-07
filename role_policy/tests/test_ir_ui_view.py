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

    # --- Security groups stripping depth tests ---

    def test_remove_security_groups_on_page_element(self):
        """Verify groups are stripped from <page> container elements too."""
        view = self.env["ir.ui.view"]
        arch = etree.fromstring(
            '<form>'
            '<notebook>'
            '<page name="sales" groups="sales_team.group_sale_manager">'
            '<field name="name"/>'
            '</page>'
            '</notebook>'
            '</form>'
        )
        view._remove_security_groups(arch)
        page = arch.xpath('//page[@name="sales"]')[0]
        self.assertNotIn(
            "groups",
            page.attrib,
            "Non-untouchable groups should be stripped from <page>",
        )

    def test_remove_security_groups_on_group_element(self):
        """Verify groups are stripped from <group> elements."""
        view = self.env["ir.ui.view"]
        arch = etree.fromstring(
            '<form>'
            '<group name="grp1" groups="account.group_account_invoice">'
            '<field name="name"/>'
            '</group>'
            '</form>'
        )
        view._remove_security_groups(arch)
        grp = arch.xpath('//group[@name="grp1"]')[0]
        self.assertNotIn("groups", grp.attrib)

    def test_remove_security_groups_preserves_multiple_untouchables(self):
        """Verify multiple untouchable groups are all preserved."""
        view = self.env["ir.ui.view"]
        arch = etree.fromstring(
            '<form>'
            '<field name="test" groups="base.group_no_one,base.group_system"/>'
            '</form>'
        )
        view._remove_security_groups(arch)
        field = arch.xpath('//field[@name="test"]')[0]
        groups = field.get("groups", "").split(",")
        self.assertIn("base.group_no_one", groups)
        self.assertIn("base.group_system", groups)

    def test_remove_security_groups_strips_from_buttons(self):
        """Verify groups are stripped from buttons."""
        view = self.env["ir.ui.view"]
        arch = etree.fromstring(
            '<form>'
            '<button name="action" groups="sales_team.group_sale_manager"/>'
            '</form>'
        )
        view._remove_security_groups(arch)
        btn = arch.xpath("//button")[0]
        self.assertNotIn("groups", btn.attrib)

    def test_handle_roles_removes_nested_elements(self):
        """Verify that removing a roles-gated element also removes children."""
        view = self.env["ir.ui.view"]
        arch = etree.fromstring(
            '<form>'
            '<group roles="NONEXISTENT">'
            '<field name="name"/>'
            '<field name="email"/>'
            '</group>'
            '<field name="phone"/>'
            '</form>'
        )
        view.with_user(self.test_user)._handle_roles(arch)
        # The entire group and its children should be gone
        self.assertEqual(len(arch.xpath("//group")), 0)
        self.assertEqual(len(arch.xpath('//field[@name="name"]')), 0)
        # But phone should still be there
        self.assertEqual(len(arch.xpath('//field[@name="phone"]')), 1)

    def test_no_access_view_arch_form(self):
        """Verify _no_access_view_arch returns form with message."""
        view = self.env["ir.ui.view"]
        result = view._no_access_view_arch({"type": "form"})
        self.assertIn("<form>", result)
        self.assertIn("not allowed", result)

    def test_no_access_view_arch_other_raises(self):
        """Verify _no_access_view_arch raises for non-form views."""
        view = self.env["ir.ui.view"]
        with self.assertRaises(NotImplementedError):
            view._no_access_view_arch({"type": "list"})
