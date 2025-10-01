# models/sale_order_line.py
from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    barcode = fields.Char(
        string='Código de Barras',
        help='Escanea o introduce el código de barras del producto'
    )

    @api.onchange('barcode')
    def _onchange_barcode(self):
        """Buscar producto por código de barras y seleccionarlo automáticamente"""
        if self.barcode:
            product = self.env['product.product'].search([
                ('barcode', '=', self.barcode),
                ('sale_ok', '=', True)
            ], limit=1)

            if product:
                self.product_id = product
                # Limpiar el barcode después de seleccionar el producto
                self.barcode = False

            else:
                # Limpiar el campo si no se encuentra el producto
                self.barcode = False
                return {
                    'warning': {
                        'title': '❌ Código no encontrado',
                        'message': f'No se encontró ningún producto con el código "{self.barcode}"'
                    }
                }
