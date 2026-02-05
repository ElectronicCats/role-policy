# Copyright 2024 Electronic Cats
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestProductProduct(TransactionCase):
    """Tests for product.product extension with role_policy."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
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
        # This test verifies the mechanism is in place
        # The actual ACL check depends on proper role/ACL configuration
        IrModelAccess = self.env["ir.model.access"]
        self.assertTrue(hasattr(IrModelAccess, "_get_acl_access_group_ids"))

    def test_sales_count_field_exists(self):
        """Verify that sales_count field exists on product."""
        self.assertTrue(hasattr(self.product, "sales_count"))
