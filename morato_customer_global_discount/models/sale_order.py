from odoo import models, api, fields, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        """Override to apply global discount when confirming sale order"""
        # Apply discount before confirming
        self._apply_global_discount_standard()
        result = super().action_confirm()
        return result

    def _apply_global_discount_standard(self):
        """Apply global discount from customer using Odoo's standard discount logic"""
        for order in self:
            # Use Odoo's standard discount wizard logic
            discount_percentage = order.partner_id.global_discount_percentage

            if discount_percentage > 0:
                # Remove existing global discount lines first
                existing_discount_lines = order.order_line.filtered(
                    lambda line: line.name and ('Discount' in line.name or 'Descuento' in line.name)
                )
                if existing_discount_lines:
                    existing_discount_lines.unlink()


                # Create a temporary wizard to use Odoo's standard logic
                wizard_vals = {
                    'sale_order_id': order.id,
                    'discount_type': 'so_discount',  # Global Discount type
                    'discount_percentage': discount_percentage,
                    'tax_ids': [(6, 0, [])],  # No taxes on discount line by default
                }

                wizard = self.env['sale.order.discount'].create(wizard_vals)

                # Apply the discount using Odoo's standard method
                wizard.action_apply_discount()
