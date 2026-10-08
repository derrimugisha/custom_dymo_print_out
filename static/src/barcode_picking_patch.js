/** @odoo-module **/

import BarcodePickingModel from "@stock_barcode/models/barcode_picking_model";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";

/**
 * Patch BarcodePickingModel to support the "Scan → Send → Validate" workflow.
 *
 * For INTERNAL transfers:
 *  - While NOT sent:   validate button shows "Send" → calls action_send on server
 *  - After "Sent":     validate button shows "Validate" → standard flow
 *
 * All other transfer types (incoming/outgoing) remain unchanged.
 */
patch(BarcodePickingModel.prototype, {

    /** Show "Send" label for unsent internal transfers */
    get validateButtonLabel() {
        if (this._isInternalUnsent()) {
            return _t("Send");
        }
        return super.validateButtonLabel;
    },

    /**
     * Intercept the validate action. For unsent internal transfers,
     * call action_send instead of the normal button_validate.
     */
    async _validate() {
        if (this._isInternalUnsent()) {
            return this._send();
        }
        return super._validate();
    },

    /** Calls action_send on the server, shows success and navigates back */
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

    /**
     * Returns true if this is an internal transfer that has NOT been sent yet.
     * Uses `this.record` which is the picking data loaded by the barcode model.
     */
    _isInternalUnsent() {
        const rec = this.record;
        return (
            rec &&
            rec.picking_type_code === "internal" &&
            !rec.is_sent
        );
    },
});
