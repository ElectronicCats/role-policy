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

    get isExportEnable() {
        if (this._rolePolicyHideExport) {
            return false;
        }
        return super.isExportEnable;
    },

    get archiveEnabled() {
        if (this._rolePolicyHideArchive) {
            return false;
        }
        return super.archiveEnabled;
    },
});
