from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_view_ticket(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/sale_order/{self.id}/ticket',
            'target': 'new',
        }

    def action_mobile_custom(self):
        """Acción personalizada para móvil que confirma el pedido, valida la entrega y crea la factura"""
        # 1. Confirmar el pedido si está en borrador
        if self.state == 'draft':
            self.action_confirm()

        # 2. Validar la entrega si existe y no está validada
        for picking in self.picking_ids:
            if picking.state in ['confirmed', 'assigned', 'waiting', 'partially_available']:
                # Marcar todos los productos como entregados (cantidad hecha = cantidad demandada)
                for move in picking.move_ids:
                    if not move.move_line_ids:
                        move.move_line_ids = [(0, 0, {
                            'product_id': move.product_id.id,
                            'location_id': move.location_id.id,
                            'location_dest_id': move.location_dest_id.id,
                            'quantity': move.product_uom_qty,
                            'product_uom_id': move.product_uom.id,
                        })]
                    move.quantity = move.product_uom_qty

                # Validar el picking
                picking.button_validate()

        # 3. Crear la factura si no existe
        if not self.invoice_ids and self.state == 'sale':
            # Ejecutar el wizard estándar de Odoo para crear la factura
            wizard = self.env['sale.advance.payment.inv'].create({
                'advance_payment_method': 'delivered',
                'sale_order_ids': [(6, 0, self.ids)],
            })
            res = wizard.create_invoices()
            # Confirmar la factura automáticamente si se ha creado
            if res and res.get('res_id'):
                invoice = self.env['account.move'].browse(res['res_id'])
                for inv_line in invoice.invoice_line_ids:
                    sale_line = inv_line.sale_line_ids and inv_line.sale_line_ids[0] or False
                    inv_line.box_units = sale_line.box_units if sale_line else 0
                    inv_line.boxes = sale_line.boxes if sale_line else 0
                invoice.action_post()

        return True

    def action_open_ticket_pos(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'sale_ticket_pos',
            'target': 'new',
            'params': {'order_id': self.id},
            'context': {'order_id': self.id},
        }
