# Copyright 2020-2021 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from lxml import etree
from odoo import api, models
from odoo.tools import config

_logger = logging.getLogger(__name__)
_logger.warning("role_policy base.py LOADED - get_view override is active")


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

    @api.model
    def get_view(self, view_id=None, view_type="form", **options):
        result = super().get_view(view_id, view_type, **options)
        if self.env.user.exclude_from_role_policy:
            return result

        rid = result.get("id")
        if not rid:
            return result

        IrUiView = self.env["ir.ui.view"].sudo()
        view = IrUiView.browse(rid)

        _logger.warning(
            "role_policy get_view: model=%s view_id=%s view_type=%s user=%s",
            self._name,
            rid,
            view_type,
            self.env.user.login,
        )

        arch = result["arch"]
        arch = view._remove_xml_comments(arch)
        arch = view._apply_view_type_attribute_rules(arch)

        archs = [(arch, view.id)]
        archs = IrUiView._apply_view_modifier_remove_rules(self._name, archs)
        archs = IrUiView._apply_view_modifier_rules(self._name, archs)

        if archs:
            arch_node = etree.fromstring(archs[0][0])
            IrUiView._remove_security_groups(arch_node)
            IrUiView._handle_roles(arch_node)
            arch = etree.tostring(arch_node, encoding="unicode")
        else:
            arch = view._no_access_view_arch({"type": view_type or view.type})

        result["arch"] = arch
        return result
