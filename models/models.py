# -*- coding: utf-8 -*-

from odoo import api, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model_create_multi
    def create(self, vals_list):
        vals_list = [vals.copy() for vals in vals_list]
        for vals in vals_list:
            if not vals.get("barcode"):
                vals["barcode"] = self._next_variant_barcode()
        return super().create(vals_list)

    def _next_variant_barcode(self):
        number = self.env["ir.sequence"].next_by_code(
            "custom_dymo_print_out.product_variant_barcode"
        )
        digits = str(number).zfill(12)
        checksum = (10 - sum(int(digit) * (1 if index % 2 == 0 else 3)
                             for index, digit in enumerate(digits)) % 10) % 10
        return f"{digits}{checksum}"

    def action_generate_missing_barcodes(self):
        for product in self.filtered(lambda record: not record.barcode):
            product.barcode = self._next_variant_barcode()
        return True
