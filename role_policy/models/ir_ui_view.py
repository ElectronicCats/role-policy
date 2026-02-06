# Copyright 2020-2024 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from lxml import etree
from odoo import _, api, models
from odoo.exceptions import UserError
from odoo.tools import safe_eval
from odoo.tools.template_inheritance import locate_node

_logger = logging.getLogger(__name__)


class IrUiView(models.Model):
    _inherit = "ir.ui.view"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not self.env.context.get("role_policy_init") and "groups_id" in vals:
                del vals["groups_id"]
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.context.get("role_policy_init") and "groups_id" in vals:
            vals = dict(vals)
            vals.pop("groups_id", None)
            if not vals:
                return True
        return super().write(vals)

    def _get_view(self, view_id=None, view_type="form", **options):
        arch, view = super()._get_view(view_id=view_id, view_type=view_type, **options)
        if self.env.user.exclude_from_role_policy:
            return arch, view

        # Use passed parameters or view dict for robustness
        v_id = view.get("id") if isinstance(view, dict) else view.id
        model = view.get("model") if isinstance(view, dict) else (view.model if hasattr(view, 'model') else self._name)

        if not model or model not in self.env:
            return arch, view

        self._apply_view_type_attribute_rules_node(arch, v_id, view_type, model)
        modified_arch = self._apply_view_modifier_remove_rules_node(arch, model, v_id)
        if modified_arch is not None:
            self._apply_view_modifier_rules_node(modified_arch, model, v_id, view_type=view_type)
            self._remove_security_groups(modified_arch)
            self._handle_roles(modified_arch)
            self._clean_arch_from_broken_fields(modified_arch, model)
            return modified_arch, view
        else:
            arch_str = self._no_access_view_arch({"type": view_type})
            return etree.fromstring(arch_str), view

    def read_combined(self, fields=None):
        res = super().read_combined(fields=fields)
        if self.env.user.exclude_from_role_policy:
            return res
        arch_node = etree.fromstring(res["arch"])
        model = self.model or self._name
        self._apply_view_type_attribute_rules_node(arch_node, self.id, self.type, model)
        arch_node = self._apply_view_modifier_remove_rules_node(arch_node, model, self.id)
        if arch_node is not None:
            self._apply_view_modifier_rules_node(arch_node, model, self.id, view_type=self.type)
            self._remove_security_groups(arch_node)
            self._handle_roles(arch_node)
            self._clean_arch_from_broken_fields(arch_node, model)
            res["arch"] = etree.tostring(arch_node, encoding="unicode")
        else:
            res["arch"] = self._no_access_view_arch(res)
        return res

    @api.model
    def apply_inheritance_specs(self, source, specs_tree, pre_locate=lambda s: True):
        """
        No Mercy inheritance: if inheritance fails, we log it and continue
        instead of crashing the whole view.
        """
        try:
            return super().apply_inheritance_specs(
                source, specs_tree, pre_locate=pre_locate
            )
        except (ValueError, TypeError):
            _logger.warning(
                "Role Policy: Inheritance application failed (probably element not found). "
                "Returning source unchanged to prevent crash."
            )
            return source

    @api.model
    def get_inheriting_views_arch(self, view_id, model):
        archs = super().get_inheriting_views_arch(view_id, model)
        if self.env.user.exclude_from_role_policy:
            return archs
        return archs

    def _remove_xml_comments(self, arch):
        if "<!--" in arch:
            try:
                s0, s1 = arch.split("<!--", 1)
                s2 = s1.split("-->", 1)[1]
                return s0 + s2
            except Exception:
                return arch
        else:
            return arch

    def _apply_view_type_attribute_rules_node(self, arch_node, view_id, view_type, model):
        vta_rules = self.env["view.type.attribute"]._get_rules(view_id)
        if vta_rules:
            [arch_node.set(r.attrib, r.attrib_val) for r in vta_rules]

        if not self.env.is_admin():
            operations = self.env["view.model.operation"]._operations_dict()
            vmo_rules = self.env["view.model.operation"]._get_rules(model=model)
            vta_attribs = vta_rules.mapped("attrib")
            for rule in vmo_rules:
                if rule.operation in vta_attribs:
                    continue
                for k, v in operations.items():
                    if k != rule.operation:
                        continue
                    view_types = v.get("view_types", [])
                    if view_type in view_types or view_type in ("tree", "list"):
                        arch_node.set(
                            v.get("view_type_attribute") or k,
                            "0" if rule.disable else "1",
                        )

    def _apply_view_modifier_remove_rules_node(self, arch_node, model, view_id):
        rules = self.env["view.modifier.rule"]._get_rules(model, view_id, remove=True)
        for rule in rules:
            if not rule.element:
                if rule.view_id:
                    return None  # Total removal
            else:
                try:
                    rule_node = etree.fromstring(f"<{rule.element}/>")
                except Exception:
                    continue
                to_remove = locate_node(arch_node, rule_node)
                if to_remove is not None:
                    parent = to_remove.getparent()
                    if parent is not None:
                        parent.remove(to_remove)
        return arch_node

    def _apply_view_modifier_rules_node(self, arch_node, model, view_id, view_type=None):
        if not model or model not in self.env:
            return
        rules = self.env["view.modifier.rule"]._get_rules(
            model, view_id, view_type=view_type or getattr(self, "type", "form")
        )
        model_obj = self.env[model]
        for rule in rules:
            el = rule.element
            try:
                if el[:5] == "xpath":
                    expr = safe_eval(el.split("expr=")[1])
                else:
                    parts = el.split(" ")
                    tag = parts[0].strip()
                    attrib, val = parts[1].strip().split("=")
                    attrib = attrib.strip()
                    val = val.strip()[1:-1]
                    expr = f"//{tag}[@{attrib}='{val}']"
                expr = f"({expr})[1]"
                nodes = arch_node.xpath(expr)
                if not nodes:
                    continue
                node = nodes[0]
                
                # Odoo 18 Paranoia: Verify that if it's a field, it exists in the model
                if node.tag == "field":
                    name = node.get("name")
                    if name and name not in model_obj._fields:
                        continue

                node.attrib.pop("attrs", None)
                for mod in [
                    "modifier_invisible",
                    "modifier_readonly",
                    "modifier_required",
                ]:
                    rule_mod = getattr(rule, mod)
                    modifier = mod[9:]
                    node_view_type = view_type or getattr(self, "type", "form")
                    if (
                        modifier == "invisible"
                        and node_view_type in ("list", "tree")
                        and node.tag == "field"
                    ):
                        modifier = "column_invisible"

                    node.attrib.pop(modifier, None)
                    if rule_mod in ["0", "1"]:
                        node.set(modifier, "True" if rule_mod == "1" else "False")
                    elif rule_mod:
                        node.set(modifier, rule_mod)
                    if (
                        mod == "modifier_readonly"
                        and node.tag == "field"
                        and rule_mod
                    ):
                        node.set("force_save", "1")
            except Exception:
                continue

    def _remove_security_groups(self, arch_node):
        untouchable_groups = self._role_policy_untouchable_groups()
        for node in arch_node.xpath("//*[@groups]"):
            groups_attr = node.attrib.get("groups")
            if not groups_attr:
                continue
            groups = groups_attr.split(",")
            untouchables = [x for x in groups if x.strip() in untouchable_groups]
            if untouchables:
                node.set("groups", ",".join(untouchables))
            else:
                node.attrib.pop("groups", None)

    def _handle_roles(self, arch_node):
        for node in arch_node.xpath("//*[@roles]"):
            roles = node.attrib.pop("roles")
            roles = roles.split(",")
            roles = [x.strip() for x in roles]
            if not any([self.env.user.has_role(r) for r in roles]):
                parent = node.getparent()
                if parent is not None:
                    parent.remove(node)

    def _clean_arch_from_broken_fields(self, arch, model):
        """
        Remove fields from arch that are not in the model registry.
        This prevents OwlError in the frontend.
        """
        if not model or model not in self.env:
            return
        
        def _recursive_clean(node, current_model):
            if not current_model or current_model not in self.env:
                return
            
            model_obj = self.env[current_model]
            fields = model_obj._fields
            for child in list(node):
                if child.tag == "field":
                    name = child.get("name")
                    if not name:
                        _logger.warning("Role Policy: Removing field node without 'name' attribute in model '%s'", current_model)
                        node.remove(child)
                        continue
                    
                    if name in fields:
                        # Recurse for relational fields
                        field = fields[name]
                        rel_model = getattr(field, "comodel_name", None)
                        if rel_model:
                             _recursive_clean(child, rel_model)
                    else:
                        # Broken technical field or legacy name
                        _logger.warning("Role Policy: Removing broken field '%s' from model '%s' (Not in server registry).", name, current_model)
                        node.remove(child)
                else:
                    _recursive_clean(child, current_model)

        _recursive_clean(arch, model)

    def _no_access_view_arch(self, view_dict):
        tag = view_dict.get("type") or "form"
        if tag == "tree":
            tag = "list"
        message = _("Your are not allowed to view this information.")
        if tag == "list":
            return f'<list><field name="id" column_invisible="True"/><button string="{message}" name="dummy" type="object"/></list>'
        elif tag == "calendar":
             return f'<calendar date_start="id"><field name="id" invisible="True"/><p>{message}</p></calendar>'
        elif tag == "kanban":
             return f'<kanban><templates><t t-name="card"><div class="oe_kanban_global_click"><p>{message}</p><field name="id" invisible="True"/></div></t></templates></kanban>'
        elif tag == "form":
            return f'<form><sheet><group><p>{message}</p></group></sheet></form>'
        else:
            return f"<{tag}><p>{message}</p></{tag}>"
