from odoo import models, fields, api
from odoo.tools import SQL

class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'

    city = fields.Char(string="Población", readonly=True)

    @api.model
    def _select(self) -> SQL:
        # Añadimos partner.city al SELECT extendiendo el original
        return SQL("%s, partner.city AS city", super()._select())
