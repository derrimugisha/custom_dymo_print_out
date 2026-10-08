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

    # Computed per-user field: tells the view and barcode app whether the
    # current user is a stock manager (supervisor/validator role).
    user_is_stock_manager = fields.Boolean(
        string="User Is Stock Manager",
        compute="_compute_user_is_stock_manager",
    )

    def _compute_user_is_stock_manager(self):
        is_manager = self.env.user.has_group("stock.group_stock_manager")
        for picking in self:
            picking.user_is_stock_manager = is_manager

    @api.depends("move_ids.state", "move_ids.picking_id", "is_sent")
    def _compute_state(self):
        super()._compute_state()
        for picking in self:
            if picking.is_sent and picking.state not in ("done", "cancel"):
                picking.state = "sent"

    def action_send(self):
        """Transition the picking to 'sent' (in transit) state.
        Only stock users (operators) should call this.
        """
        for picking in self:
            if self.env.user.has_group("stock.group_stock_manager"):
                raise UserError(
                    _("Managers cannot send transfers. This action is for warehouse operators only.")
                )
            if picking.state not in ("assigned", "confirmed"):
                raise UserError(_("You can only send transfers that are ready or confirmed."))
            picking.is_sent = True
            picking.state = "sent"
            picking.message_post(body=_("Transfer has been sent and is in transit."))
        return True

    def button_validate(self):
        """Validate internal transfers — restricted to stock managers only."""
        for picking in self:
            if picking.picking_type_code == "internal":
                if not picking.is_sent:
                    raise UserError(_("Please send this transfer before validating."))
                if not self.env.user.has_group("stock.group_stock_manager"):
                    raise UserError(
                        _("Only stock managers (supervisors) can validate internal transfers.")
                    )
        return super().button_validate()

    def _get_fields_stock_barcode(self):
        flds = super()._get_fields_stock_barcode()
        for f in ("is_sent", "user_is_stock_manager"):
            if f not in flds:
                flds.append(f)
        return flds