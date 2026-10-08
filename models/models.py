# -*- coding: utf-8 -*-

from odoo import api, models

DEFAULT_BASE_BARCODE = "010010106562"


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.depends("product_variant_ids.barcode")
    def _compute_barcode(self):
        """Keep the base barcode available on the template even when variants exist.

        Standard Odoo wipes template.barcode to False when len(variants) > 1.
        Here we retain the base barcode so newly added variants can always read it.
        """
        for template in self:
            variants = template.product_variant_ids
            if len(variants) == 1:
                template.barcode = variants.barcode
            elif len(variants) > 1:
                first_barcode = next((v.barcode for v in variants if v.barcode), False)
                if first_barcode and len(first_barcode) > 3:
                    template.barcode = first_barcode[:-3]
                else:
                    template.barcode = first_barcode
            else:
                template.barcode = False

    @api.model_create_multi
    def create(self, vals_list):
        templates = super().create(vals_list)
        for template, vals in zip(templates, vals_list):
            raw_base = vals.get("barcode")
            if raw_base and len(template.product_variant_ids) > 1:
                for variant in template.product_variant_ids:
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
                )
        return super().create(vals_list)

    def _next_variant_barcode(self, product_tmpl_id=None, base_code=None):
        base = base_code
        tmpl = None

        if not base and self:
            tmpl = self.product_tmpl_id
        elif not base and product_tmpl_id:
            tmpl = self.env["product.template"].browse(product_tmpl_id)

        # 1. Read base barcode from template
        if not base and tmpl and tmpl.exists() and tmpl.barcode:
            base = tmpl.barcode

        # 2. If template barcode was empty, read base barcode from existing variants
        if not base and tmpl and tmpl.exists():
            existing = self.env["product.product"].search([
                ("product_tmpl_id", "=", tmpl.id),
                ("barcode", "!=", False),
            ], order="id asc", limit=1)
            if existing and existing.barcode:
                if len(existing.barcode) > 3:
                    base = existing.barcode[:-3]
                else:
                    base = existing.barcode

        # 3. Fallback to default base barcode
        if not base:
            base = DEFAULT_BASE_BARCODE

        number = self.env["ir.sequence"].next_by_code(
            "custom_dymo_print_out.product_variant_barcode"
        )
        if not number:
            return False

        # Strictly format to a 3-digit serial extension
        digits_only = "".join(filter(str.isdigit, str(number)))
        seq_int = int(digits_only) if digits_only else 0
        seq_str = f"{seq_int:03d}"

        base_str = str(base).strip()
        # If base already has a 3-digit serial extension (15 digits), retain the 12-digit base
        if len(base_str) == 15:
            base_str = base_str[:12]

        return f"{base_str}{seq_str}"

    def action_generate_missing_barcodes(self):
        for product in self.filtered(lambda record: not record.barcode or len(record.barcode) <= 3):
            product.barcode = product._next_variant_barcode()
        return True
