from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    partner_city = fields.Char(related='partner_id.city', store=True, string='Población')

