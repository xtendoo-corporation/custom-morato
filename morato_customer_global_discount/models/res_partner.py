from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    global_discount_percentage = fields.Float(
        string='Global Discount (%)',
        help='Global discount percentage to apply on sales orders and invoices',
        default=0.0,
        digits=(5, 2)
    )
