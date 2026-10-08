/** @odoo-module **/

import BarcodePickingModel from "@stock_barcode/models/barcode_picking_model";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";

/**
 * Patch BarcodePickingModel to enforce the "Scan → Send → Validate" workflow
 * with strict role separation:
 *
 *  OPERATOR (stock user, NOT manager):
 *    - Sees "Send" button for internal transfers that are not yet sent
 *    - Cannot see/use "Validate" for internal transfers
 *
 *  MANAGER (stock manager / supervisor):
 *    - Sees "Validate" button only after the transfer has been sent
 *    - Cannot see/use "Send"
 *
 * All non-internal transfer types (incoming/outgoing) remain unchanged.
 */
patch(BarcodePickingModel.prototype, {

    /** Button label based on role and transfer state */
    get validateButtonLabel() {
        if (this._isInternalUnsent() && !this._isManager()) {
            return _t("Send");
        }
        return super.validateButtonLabel;
    },

    /**
     * Control whether the validate/send button should be displayed.
     * - Operators: show "Send" only when transfer is unsent internal
     * - Managers:  show "Validate" only when transfer has been sent
     * - Non-internal: standard Odoo behavior
     */
    get displayValidateButton() {
        const rec = this.record;
        if (!rec || rec.picking_type_code !== "internal") {
            return super.displayValidateButton;
        }
        if (this._isManager()) {
            // Manager sees Validate only after it was sent
            return rec.is_sent;
        }
        // Operator sees Send only while it hasn't been sent yet
        return !rec.is_sent;
    },

    /**
     * Intercept the validate/send action based on role:
     *  - Operator on unsent internal → calls action_send
     *  - Manager on sent internal    → calls standard button_validate
     */
    async _validate() {
        if (this._isInternalUnsent() && !this._isManager()) {
            return this._send();
        }
        return super._validate();
    },

    /** Calls action_send on the server and navigates back */
    async _send() {
        await this.save();
        await this.orm.call(
            this.resModel,
            "action_send",
            [this.recordIds],
            {}
        );
        this.notification(_t("Transfer sent. It is now in transit."), { type: "success" });
        this.trigger("history-back");
    },

    /** True when this is an internal transfer that has NOT been sent yet */
    _isInternalUnsent() {
        const rec = this.record;
        return rec && rec.picking_type_code === "internal" && !rec.is_sent;
    },

    /** True when the current user is a stock manager (supervisor) */
    _isManager() {
        const rec = this.record;
        return rec && rec.user_is_stock_manager;
    },
});
