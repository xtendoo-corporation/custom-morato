from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    partner_city = fields.Char(related='partner_id.city', store=True, string='Población')
