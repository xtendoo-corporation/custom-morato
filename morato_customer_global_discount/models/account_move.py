from odoo import models, api, fields, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        """Override to apply global discount when posting invoice"""
        # Apply discount before posting
        self._apply_global_discount_standard()
        result = super().action_post()
        return result

    def _apply_global_discount_standard(self):
        """Apply global discount from customer to the invoice using standard logic"""
        for move in self:
            if (move.move_type in ('out_invoice', 'out_refund') and
                move.partner_id.global_discount_percentage > 0 and
                move.state == 'draft'):

                # Remove existing global discount lines first
                existing_discount_lines = move.invoice_line_ids.filtered(
                    lambda line: line.name and ('Discount' in line.name or 'Descuento' in line.name)
                )
                if existing_discount_lines:
                    existing_discount_lines.unlink()

                # Get or create discount product using company's discount product
                discount_product = self._get_company_discount_product()

                # Calculate discount using similar logic to sale.order.discount wizard
                discount_percentage = move.partner_id.global_discount_percentage / 100

                # Group lines by tax to create appropriate discount lines
                self._create_invoice_discount_lines(discount_product, discount_percentage)

    def _get_company_discount_product(self):
        """Get company's discount product or create one if it doesn't exist"""
        discount_product = self.company_id.sale_discount_product_id
        if not discount_product:
            # Create discount product using Odoo's standard structure
            discount_product_vals = {
                'name': _('Discount'),
                'detailed_type': 'service',
                'invoice_policy': 'order',
                'list_price': 0.0,
                'company_id': self.company_id.id,
                'taxes_id': [(5, 0, 0)],  # No taxes
                'supplier_taxes_id': [(5, 0, 0)],  # No taxes
            }
            discount_product = self.env['product.product'].create(discount_product_vals)
            # Set it as company's discount product
            self.company_id.sale_discount_product_id = discount_product
        return discount_product

    def _create_invoice_discount_lines(self, discount_product, discount_percentage):
        """Create discount lines for invoice using tax grouping logic"""
        from collections import defaultdict

        total_price_per_tax_groups = defaultdict(float)

        # Group invoice lines by taxes (similar to sale.order.discount wizard)
        for line in self.invoice_line_ids:
            if not line.quantity or not line.price_unit or line.display_type:
                continue
            # Skip lines that are already discount lines
            if line.name and ('Discount' in line.name or 'Descuento' in line.name):
                continue

            # Fixed taxes cannot be discounted
            taxes = line.tax_ids.flatten_taxes_hierarchy()
            fixed_taxes = taxes.filtered(lambda t: t.amount_type == 'fixed')
            taxes -= fixed_taxes
            total_price_per_tax_groups[taxes] += line.price_unit * line.quantity

        if not total_price_per_tax_groups:
            return

        # Create discount lines
        discount_dp = self.env['decimal.precision'].precision_get('Discount')

        if len(total_price_per_tax_groups) == 1:
            # Single tax group
            taxes = next(iter(total_price_per_tax_groups.keys()))
            subtotal = total_price_per_tax_groups[taxes]

            discount_line_vals = {
                'move_id': self.id,
                'product_id': discount_product.id,
                'name': _("Discount %(percent)s%%",
                         percent=f"{discount_percentage * 100:.{discount_dp}f}"),
                'quantity': 1,
                'price_unit': -(subtotal * discount_percentage),
                'tax_ids': [(6, 0, taxes.ids)],
                'sequence': 999,
            }

            # Set account for the discount line
            account = discount_product.property_account_income_id or \
                     discount_product.categ_id.property_account_income_categ_id
            if account:
                discount_line_vals['account_id'] = account.id

            self.env['account.move.line'].create(discount_line_vals)
        else:
            # Multiple tax groups - create separate discount line for each
            for taxes, subtotal in total_price_per_tax_groups.items():
                discount_line_vals = {
                    'move_id': self.id,
                    'product_id': discount_product.id,
                    'name': _("Discount %(percent)s%% - On products with taxes %(taxes)s",
                             percent=f"{discount_percentage * 100:.{discount_dp}f}",
                             taxes=", ".join(taxes.mapped('name'))),
                    'quantity': 1,
                    'price_unit': -(subtotal * discount_percentage),
                    'tax_ids': [(6, 0, taxes.ids)],
                    'sequence': 999,
                }

                # Set account for the discount line
                account = discount_product.property_account_income_id or \
                         discount_product.categ_id.property_account_income_categ_id
                if account:
                    discount_line_vals['account_id'] = account.id

                self.env['account.move.line'].create(discount_line_vals)
