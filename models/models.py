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


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model_create_multi
    def create(self, vals_list):
        """Keep a barcode given on the product itself (form, import).

        The variant is created first and gets an automatic barcode; Odoo then
        only copies the template's barcode down when the variant has none, so
        the one that was typed or imported would be dropped.
        """
        templates = super().create(vals_list)
        for template, vals in zip(templates, vals_list):
            if vals.get("barcode") and template.barcode != vals["barcode"]:
                template.barcode = vals["barcode"]
        return templates
