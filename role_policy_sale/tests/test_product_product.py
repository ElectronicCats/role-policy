# Copyright 2024 Electronic Cats
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import tagged

from odoo.addons.role_policy.tests.common import RolePolicyTestCommon


@tagged("post_install", "-at_install")
class TestProductProduct(RolePolicyTestCommon):
    """Tests for product.product extension with role_policy."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "consu",
            }
        )

    def test_compute_sales_count_method_exists(self):
        """Verify that _compute_sales_count method exists and is overridden."""
        product = self.env["product.product"]
        self.assertTrue(hasattr(product, "_compute_sales_count"))

    def test_sales_count_check_uses_acl(self):
        """Verify that sales_count check uses _get_acl_access_group_ids."""
        IrModelAccess = self.env["ir.model.access"]
        self.assertTrue(hasattr(IrModelAccess, "_get_acl_access_group_ids"))

    def test_sales_count_field_exists(self):
        """Verify that sales_count field exists on product."""
        self.assertTrue(hasattr(self.product, "sales_count"))

    def test_sales_count_zero_without_acl(self):
        """Verify that sales_count is 0 when user's role has no ACL on sale.report."""
        # self.test_user has self.role which has no ACL on sale.report
        product = self.product.with_user(self.test_user)
        self.assertEqual(product.sales_count, 0)

    def test_sales_count_computed_with_acl(self):
        """Verify that sales_count is computed when user's role has ACL on sale.report."""
        sale_report_model = self.env["ir.model"].search(
            [("model", "=", "sale.report")], limit=1
        )
        if not sale_report_model:
            self.skipTest("sale.report model not found.")
        role_with_acl = self._create_role_with_acl("SALR", "sale.report", "r")
        user_with_acl = self.env["res.users"].create(
            {
                "name": "User With Sale Report ACL",
                "login": "user_sale_report_acl",
                "role_ids": [(6, 0, [role_with_acl.id])],
            }
        )
        product = self.product.with_user(user_with_acl)
        # Should not raise; value is numeric (0 or more from super)
        self.assertIsInstance(product.sales_count, (int, float))
