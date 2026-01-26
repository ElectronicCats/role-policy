# Copyright 2020-2024 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_post(self):
        """Override action_post to check role policy execution rights.

        Note: In Odoo 15+, the method was renamed from post() to action_post().
        """
        self.env["model.method.execution.right"].check_right(
            "account.move,action_post", raise_exception=True
        )
        ctx = dict(self.env.context, role_policy_has_groups_ok=True)
        self = self.with_context(ctx)
        return super().action_post()
