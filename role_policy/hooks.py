# Copyright 2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def post_init_hook(env):
    """
    Remove groups from menuitems, views, actions and users since the standard groups
    are replaced by role groups when installing this module.

    WARNING: This hook performs DESTRUCTIVE operations on installation!
    ==================================================================
    It removes ALL group associations from:
    - All menu items (ir.ui.menu)
    - All views (ir.ui.view)
    - All window actions (ir.actions.act_window)
    - All server actions (ir.actions.server)
    - All report actions (ir.actions.report)
    - All internal users (except admin and root)

    After installation, you MUST configure roles and assign them to users
    for the system to work properly. Without roles, non-admin users will
    have very limited access to the system.

    This behavior is by design: the Role Policy module replaces Odoo's
    standard group-based access control with a role-based approach.
    """
    ctx_env = env(context=dict(env.context, active_test=False, role_policy_init=True))
    menus = ctx_env["ir.ui.menu"].search([])
    menus.write({"groups_id": [(5,)]})
    views = ctx_env["ir.ui.view"].search([])
    views.write({"groups_id": [(5,)]})
    for act_model in [
        "ir.actions.act_window",
        "ir.actions.server",
        "ir.actions.report",
    ]:
        actions = ctx_env[act_model].search([])
        actions.write({"groups_id": [(5,)]})
    users = ctx_env["res.users"].search([("share", "=", False)])
    users -= ctx_env.ref("base.user_admin")
    users -= ctx_env.ref("base.user_root")
    for user in users:
        toremove = user.groups_id.filtered(lambda r: r != r.env.ref("base.group_user"))
        user.groups_id = [(3, x.id) for x in toremove]
