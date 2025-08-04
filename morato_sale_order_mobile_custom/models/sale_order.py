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
        """Acción personalizada para móvil que confirma el pedido"""
        if self.state == 'draft':
            self.action_confirm()
        elif self.state in ['sent', 'sale']:
            # Si ya está confirmado, podemos crear la entrega si no existe
            if not self.picking_ids and self.order_line.filtered(lambda l: l.product_id.type in ['product', 'consu']):
                self.action_confirm()
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
