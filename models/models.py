# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    base_barcode = fields.Char("Base Barcode", copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        vals_list = [vals.copy() for vals in vals_list]
        for vals in vals_list:
            if vals.get("barcode"):
                vals["base_barcode"] = vals["barcode"]
        templates = super().create(vals_list)
        for template, vals in zip(templates, vals_list):
            raw_base = vals.get("barcode") or vals.get("default_code") or template.base_barcode
            if raw_base:
                template.base_barcode = raw_base
                variants = template.product_variant_ids
                if len(variants) == 1:
                    variants[0].barcode = raw_base
                elif len(variants) > 1:
                    for variant in variants:
                        variant.barcode = variant._next_variant_barcode(base_code=raw_base)
        return templates

    def write(self, vals):
        if vals.get("barcode"):
            vals["base_barcode"] = vals["barcode"]
        res = super().write(vals)
        if "barcode" in vals or "default_code" in vals or "base_barcode" in vals:
            for template in self:
                raw_base = template.base_barcode or template.default_code
                if raw_base and len(template.product_variant_ids) > 1:
                    for variant in template.product_variant_ids:
                        if not variant.barcode or not variant.barcode.startswith(raw_base):
                            variant.barcode = variant._next_variant_barcode(base_code=raw_base)
        return res

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
        if not base_code:
            base_code = default_code
        if not base_code and self:
            tmpl = self.product_tmpl_id
            base_code = (
                getattr(tmpl, "base_barcode", False)
                or tmpl.barcode
                or tmpl.default_code
                or self.default_code
            )
        if not base_code and product_tmpl_id:
            tmpl = self.env["product.template"].browse(product_tmpl_id)
            if tmpl.exists():
                base_code = (
                    getattr(tmpl, "base_barcode", False)
                    or tmpl.barcode
                    or tmpl.default_code
                )

        # Ensure the sequence in database has padding=3
        seq = self.env["ir.sequence"].search(
            [("code", "=", "custom_dymo_print_out.product_variant_barcode")],
            limit=1,
        )
        if seq and seq.padding != 3:
            seq.sudo().write({"padding": 3})

        number = self.env["ir.sequence"].next_by_code(
            "custom_dymo_print_out.product_variant_barcode"
        )
        if not number:
            return False

        # Strictly extract only numeric digits and format to exactly 3 digits
        digits_only = "".join(filter(str.isdigit, str(number)))
        seq_int = int(digits_only) if digits_only else 0
        seq_str = f"{seq_int:03d}"

        if base_code:
            base_str = str(base_code).strip()
            # If base_str already has a 3-digit serial extension (15 digits), retain only base 12 digits
            if len(base_str) == 15:
                base_str = base_str[:12]
            return f"{base_str}{seq_str}"

        return seq_str

    def action_generate_missing_barcodes(self):
        for product in self.filtered(lambda record: not record.barcode):
            product.barcode = product._next_variant_barcode()
        return True
