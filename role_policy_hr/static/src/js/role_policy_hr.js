/** @odoo-module **/
/*
 * Copyright 2020-2024 Noviat.
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
 */

import {FormController} from "@web/views/form/form_controller";
import {patch} from "@web/core/utils/patch";

/**
 * Role Policy HR patch for Odoo 18
 * Reloads the page when saving user preferences to apply role changes
 */

patch(FormController.prototype, {
    async onRecordSaved(record) {
        const result = await super.onRecordSaved(...arguments);

        // Reload page when saving user profile to apply role changes
        if (record.resModel === "res.users" && this.props.context?.from_my_profile) {
            window.location.reload();
        }

        return result;
    },
});
