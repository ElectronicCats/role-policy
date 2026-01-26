# Copyright 2020-2021 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, models
from odoo.tools import config

_logger = logging.getLogger(__name__)


class BaseModel(models.AbstractModel):
    _inherit = "base"

    def _role_policy_untouchable_groups(self):
        """
        The role policy will remove all groups from the fields
        except the ones defined in this method.
        """
        return [
            "base.group_no_one",
            "base.group_user",
            "base.group_erp_manager",
            "base.group_system",
            "base.group_portal",
            "base.group_public",
        ]

    def _get_role_policy_group_keep_ids(self):
        group_user = self.env.ref("base.group_user")
        keep_ids = [
            self.env.ref(x).id for x in self._role_policy_untouchable_groups()
        ] + [group_user.id]
        return keep_ids

    def _role_policy_check_group(self, group_ext_id):
        """
        Check if a group should be considered for role policy.
        Returns True if the group check should pass, False to delegate to standard check.
        """
        user = self.env.user
        if (
            user.exclude_from_role_policy
            or user == self.env.ref("base.public_user")
            or config.get("test_enable")
        ):
            return None  # Delegate to standard behavior

        # Handle negation prefix
        xml_id = group_ext_id[1:] if group_ext_id.startswith("!") else group_ext_id

        if xml_id in self._role_policy_untouchable_groups():
            return None  # Delegate to standard behavior

        group = self.env.ref(xml_id, raise_if_not_found=False)
        if group and group.role:
            return None  # Delegate to standard behavior

        # For non-role groups, grant access
        return True
