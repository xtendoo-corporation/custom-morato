# -*- coding: utf-8 -*-

from odoo import models, fields


class ProductProduct(models.Model):
    _inherit = 'product.product'

    box_units = fields.Float(
        string='Units per Box',
        help='Number of units contained in one box',
        related='product_tmpl_id.box_units',
        store=True
    )

    def _get_product_catalog_record_lines(self, **kwargs):
        """
        Override to include box_units field in product catalog data
        """
        lines = super()._get_product_catalog_record_lines(**kwargs)

        # Add box_units to the product data from product template
        for line in lines:
            if line.get('id') == self.id:
                # Get box_units from the product template
                line['box_units'] = self.product_tmpl_id.box_units

        return lines


class ProductCatalogMixin(models.AbstractModel):
    _inherit = 'product.catalog.mixin'

    def _get_product_catalog_record_lines(self, products, **kwargs):
        """
        Override to include box_units field in product catalog data
        """
        lines = super()._get_product_catalog_record_lines(products, **kwargs)

        # Add box_units to each product line from product template
        for line in lines:
            product_id = line.get('id')
            if product_id:
                product = products.filtered(lambda p: p.id == product_id)
                if product:
                    # Get box_units from the product template
                    line['box_units'] = product.product_tmpl_id.box_units

        return lines
