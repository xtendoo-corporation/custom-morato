{
    'name': 'Morato Customer Global Discount',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'summary': 'Applies global discount percentage from customer to sales orders and invoices using Odoo standard logic',
    'description': """
        This module allows setting a global discount percentage on customer records.
        When confirming a sale order or posting an invoice, the customer's global
        discount percentage is automatically applied using Odoo's standard discount logic.

        Features:
        - Add global discount percentage field to customer form
        - Automatically apply discount when confirming sale orders using Odoo's standard wizard logic
        - Automatically apply discount when posting invoices using similar standard logic
        - Uses Odoo's company discount product and standard discount calculations
        - Supports proper tax handling and grouping as in Odoo's native discount feature
    """,
    'author': 'Xtendoo Software SLU',
    'website': 'https://www.xtendoo.es',
    'license': 'LGPL-3',
    'depends': [
        'sale',
        'account',
        'product',
    ],
    'data': [
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
