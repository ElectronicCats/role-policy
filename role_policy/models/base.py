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

    @api.model
    def get_view(self, view_id=None, view_type="form", **options):
        """
        Final safety net for Odoo 18 OwlError.
        Removes fields from arch that are not in the 'models' dictionary.
        """
        result = super().get_view(view_id=view_id, view_type=view_type, **options)
        if self.env.user.exclude_from_role_policy:
            return result

        arch_str = result.get("arch")
        models_info = result.get("models")
        if models_info is None:
            models_info = {}
            result["models"] = models_info

        # Odoo 18 compatibility: main model fields are often in 'fields' key
        if "fields" in result and self._name not in models_info:
            models_info[self._name] = {"fields": result["fields"]}

        if not arch_str or not models_info:
            return result

        from lxml import etree
        try:
            arch_node = etree.fromstring(arch_str)
            modified = False

            def _get_available_fields(model_name):
                """
                Returns a set of field names available for the model in models_info.
                Returns None if the model itself is not found in models_info.
                """
                if not models_info or model_name not in models_info:
                    return None
                
                model_data = models_info[model_name]
                if "fields" in model_data and isinstance(model_data["fields"], dict):
                    return set(model_data["fields"].keys())

                # Fallback: Deep search for anything that looks like a field dictionary
                candidates = []
                def _find_field_candidates(data):
                    if isinstance(data, dict):
                        # Heuristic: dict of dicts where at least one has 'type'
                        field_count = sum(
                            1 for v in data.values() 
                            if isinstance(v, dict) and "type" in v
                        )
                        if field_count > 0:
                            candidates.append(data)
                        
                        for v in data.values():
                            _find_field_candidates(v)
                    elif isinstance(data, (list, tuple)):
                        for item in data:
                            _find_field_candidates(item)

                _find_field_candidates(model_data)
                
                if not candidates:
                    return None
                
                # Pick the dictionary with the most keys
                best_fields = max(candidates, key=len)
                return set(best_fields.keys())

            def _clean_node(node, current_model):
                nonlocal modified
                if not current_model:
                    return

                available_fields = _get_available_fields(current_model)
                
                for child in list(node):
                    if child.tag == "field":
                        name = child.get("name")
                        if not name:
                            _logger.debug("Role Policy: Removing nameless field node in model '%s'", current_model)
                            node.remove(child)
                            modified = True
                            continue

                        # Odoo 18 Owl Safety: If we have model info for this model,
                        # the field MUST be in it.
                        if available_fields is not None:
                            if name not in available_fields:
                                _logger.warning(
                                    "Role Policy: Removing field '%s' from model '%s' arch "
                                    "(Missing from client fields info - Owl Safety).",
                                    name, current_model
                                )
                                node.remove(child)
                                modified = True
                                continue
                        else:
                            # CRITICAL for Odoo 18: If we don't have model info, 
                            # we check if it's a known field on the server.
                            # If it's NOT on the server, we MUST remove it.
                            # If it IS on the server but missing from client info, 
                            # it might still cause the OwlError.
                            server_model = self.env.get(current_model)
                            if server_model is not None:
                                if name not in server_model._fields:
                                    _logger.warning(
                                        "Role Policy: Removing ghost field '%s' from model '%s' (Not in registry).",
                                        name, current_model
                                    )
                                    node.remove(child)
                                    modified = True
                                    continue
                                else:
                                    # Field exists on server but we have no client info for this model.
                                    # This is Risky. We remove it to be safe if it's not the main model.
                                    if current_model != self._name:
                                        _logger.warning(
                                            "Role Policy: Removing field '%s' from sub-model '%s' "
                                            "(No client info available, avoiding OwlError).",
                                            name, current_model
                                        )
                                        node.remove(child)
                                        modified = True
                                        continue

                        # Recurse for relational fields
                        server_model = self.env.get(current_model)
                        if server_model is not None:
                            field = server_model._fields.get(name)
                            rel_model = getattr(field, "comodel_name", None)
                            if rel_model:
                                _clean_node(child, rel_model)
                    else:
                        _clean_node(child, current_model)

            _clean_node(arch_node, self._name)

            if modified:
                result["arch"] = etree.tostring(arch_node, encoding="unicode")
        except Exception:
            _logger.exception("Role Policy: Error in get_view cleanup")

        return result
