# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    is_sent = fields.Boolean(
        string="Is Sent",
        copy=False,
        default=False,
        tracking=True,
    )
    state = fields.Selection(
        selection_add=[("sent", "Sent / In Transit")],
        ondelete={"sent": "set draft"},
    )

    @api.depends("move_ids.state", "move_ids.picking_id", "is_sent")
    def _compute_state(self):
        super()._compute_state()
        for picking in self:
            if picking.is_sent and picking.state not in ("done", "cancel"):
                picking.state = "sent"

    def action_send(self):
        """Transition the picking to 'sent' (in transit) state."""
        for picking in self:
            if picking.state not in ("assigned", "confirmed"):
                raise UserError(_("You can only send transfers that are ready or confirmed."))
            picking.is_sent = True
            picking.state = "sent"
            picking.message_post(body=_("Transfer has been sent and is in transit."))
        return True

    def button_validate(self):
        """Validate internal transfers — open to all permitted stock users."""
        for picking in self:
            if picking.picking_type_code == "internal":
                if not picking.is_sent:
                    raise UserError(_("Please send this transfer before validating."))
        return super().button_validate()

    def _get_fields_stock_barcode(self):
        flds = super()._get_fields_stock_barcode()
        if "is_sent" not in flds:
            flds.append("is_sent")
        return flds