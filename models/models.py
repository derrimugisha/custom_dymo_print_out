# -*- coding: utf-8 -*-

from odoo import api, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model_create_multi
    def create(self, vals_list):
        templates = super().create(vals_list)
        for template, vals in zip(templates, vals_list):
            raw_base = vals.get("barcode") or vals.get("default_code")
            if raw_base:
                variants = template.product_variant_ids
                if len(variants) == 1:
                    variants.barcode = raw_base
                elif len(variants) > 1:
                    for variant in variants:
                        variant.barcode = variant._next_variant_barcode(base_code=raw_base)
        return templates

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

    def _next_variant_barcode(self, product_tmpl_id=None, default_code=None, base_code=None):
        base = base_code or default_code
        if not base and self:
            tmpl = self.product_tmpl_id
            base = tmpl.barcode or tmpl.default_code or self.default_code
        if not base and product_tmpl_id:
            tmpl = self.env["product.template"].browse(product_tmpl_id)
            if tmpl.exists():
                base = tmpl.barcode or tmpl.default_code

        number = self.env["ir.sequence"].next_by_code(
            "custom_dymo_print_out.product_variant_barcode"
        )
        if not number:
            return False

        # Strictly take only the numeric digits and format to a 3-digit serial extension
        digits_only = "".join(filter(str.isdigit, str(number)))
        seq_int = int(digits_only) if digits_only else 0
        seq_str = f"{seq_int:03d}"

        if base:
            base_str = str(base).strip()
            # If base already has a 3-digit serial extension (15 digits), retain the 12-digit base
            if len(base_str) == 15:
                base_str = base_str[:12]
            return f"{base_str}{seq_str}"

        return seq_str

    def action_generate_missing_barcodes(self):
        for product in self.filtered(lambda record: not record.barcode):
            product.barcode = product._next_variant_barcode()
        return True
