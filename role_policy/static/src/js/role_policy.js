/** @odoo-module **/
/*
 * Copyright 2020-2024 Noviat.
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
 */

import {KanbanController} from "@web/views/kanban/kanban_controller";
import {ListController} from "@web/views/list/list_controller";
import {patch} from "@web/core/utils/patch";
import {session} from "@web/session";

/**
 * Role Policy patches for Odoo 18
 * These patches control visibility of buttons based on role policy settings
 *
 * Note: In Odoo 18, many properties like isExportEnable and archiveEnabled
 * are read-only getters. We intercept at the action menu level instead.
 */

// Patch KanbanController to handle create/import button visibility
patch(KanbanController.prototype, {
    setup() {
        super.setup(...arguments);
        this._applyRolePolicyRestrictions();
    },

    _applyRolePolicyRestrictions() {
        if (session.exclude_from_role_policy) {
            return;
        }
        const modelOperations = session.model_operations || {};

        // Check create operation
        if (modelOperations.create) {
            const createOps = modelOperations.create;
            if (this.props.resModel in createOps) {
                this._rolePolicyHideCreate = createOps[this.props.resModel];
            } else if ("default" in createOps) {
                this._rolePolicyHideCreate = createOps.default;
            }
        }

        // Check import operation
        if (modelOperations.import) {
            const importOps = modelOperations.import;
            if (this.props.resModel in importOps) {
                this._rolePolicyHideImport = importOps[this.props.resModel];
            } else if ("default" in importOps) {
                this._rolePolicyHideImport = importOps.default;
            }
        }
    },

    get canCreate() {
        if (this._rolePolicyHideCreate) {
            return false;
        }
        return super.canCreate;
    },
});

// Patch ListController to handle export and other operations
patch(ListController.prototype, {
    setup() {
        super.setup(...arguments);
        this._applyRolePolicyRestrictions();
    },

    _applyRolePolicyRestrictions() {
        if (session.exclude_from_role_policy) {
            return;
        }
        const modelOperations = session.model_operations || {};

        // Store flags for role policy restrictions
        this._rolePolicyHideExport = false;
        this._rolePolicyHideCreate = false;
        this._rolePolicyHideImport = false;
        this._rolePolicyHideArchive = false;

        // Check export operation
        if (modelOperations.export) {
            const exportOps = modelOperations.export;
            if (this.props.resModel in exportOps) {
                this._rolePolicyHideExport = exportOps[this.props.resModel];
            } else if ("default" in exportOps) {
                this._rolePolicyHideExport = exportOps.default;
            }
        }

        // Check create operation
        if (modelOperations.create) {
            const createOps = modelOperations.create;
            if (this.props.resModel in createOps) {
                this._rolePolicyHideCreate = createOps[this.props.resModel];
            } else if ("default" in createOps) {
                this._rolePolicyHideCreate = createOps.default;
            }
        }

        // Check import operation
        if (modelOperations.import) {
            const importOps = modelOperations.import;
            if (this.props.resModel in importOps) {
                this._rolePolicyHideImport = importOps[this.props.resModel];
            } else if ("default" in importOps) {
                this._rolePolicyHideImport = importOps.default;
            }
        }

        // Check archive operation
        if (modelOperations.archive) {
            const archiveOps = modelOperations.archive;
            if (this.props.resModel in archiveOps) {
                this._rolePolicyHideArchive = archiveOps[this.props.resModel];
            } else if ("default" in archiveOps) {
                this._rolePolicyHideArchive = archiveOps.default;
            }
        }
    },

    get canCreate() {
        if (this._rolePolicyHideCreate) {
            return false;
        }
        return super.canCreate;
    },

    // Override getActionMenuItems to control export, archive and other actions
    getActionMenuItems() {
        const items = super.getActionMenuItems();
        if (!items) {
            return items;
        }

        const result = {...items};

        // Filter export action
        if (this._rolePolicyHideExport && result.other) {
            result.other = result.other.filter((item) => item.key !== "export");
        }

        // Filter archive/unarchive actions
        if (this._rolePolicyHideArchive && result.other) {
            result.other = result.other.filter(
                (item) => item.key !== "archive" && item.key !== "unarchive"
            );
        }

        return result;
    },
});
