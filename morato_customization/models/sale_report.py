from odoo import models, fields

class SaleReport(models.Model):
    _inherit = 'sale.report'

    city = fields.Char(string="Población", readonly=True)

    def _select_additional_fields(self):
        res = super()._select_additional_fields()
        res['city'] = 's.partner_city'
        return res

    def _group_by_sale(self):
        res = super()._group_by_sale()
        res += ', s.partner_city'
        return res
