# -*- coding: utf-8 -*-

from odoo import api, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def action_generate_missing_barcodes(self):
        return self.mapped("product_variant_ids").action_generate_missing_barcodes()


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model_create_multi
    def create(self, vals_list):
        vals_list = [vals.copy() for vals in vals_list]
        for vals in vals_list:
            if not vals.get("barcode"):
                tmpl_id = vals.get("product_tmpl_id") or self.env.context.get(
                    "default_product_tmpl_id"
                )
                vals["barcode"] = self._next_variant_barcode(
                    product_tmpl_id=tmpl_id,
                    default_code=vals.get("default_code"),
                )
        return super().create(vals_list)

    def _next_variant_barcode(self, product_tmpl_id=None, default_code=None):
        base_code = default_code
        if not base_code and self:
            base_code = (
                self.product_tmpl_id.barcode
                or self.product_tmpl_id.default_code
                or self.default_code
            )
        if not base_code and product_tmpl_id:
            tmpl = self.env["product.template"].browse(product_tmpl_id)
            if tmpl.exists():
                base_code = tmpl.barcode or tmpl.default_code

        number = self.env["ir.sequence"].next_by_code(
            "custom_dymo_print_out.product_variant_barcode"
        )
        if not number:
            return False

        seq_str = str(number).strip().zfill(3)

        if base_code:
            base_str = str(base_code).strip()
            return f"{base_str}{seq_str}"

        return seq_str

    def action_generate_missing_barcodes(self):
        for product in self.filtered(lambda record: not record.barcode):
            product.barcode = product._next_variant_barcode()
        return True
