# -*- coding: utf-8 -*-
{
    'name': 'Morato Sale Order Mobile Custom',
    'version': '18.0.1.0.0',
    'summary': 'Módulo personalizado para simplificar las ventas en vista móvil con formato de ticket',
    'description': """
        Este módulo personaliza la vista móvil de pedidos de venta para hacerla más simple y funcional:
        - Oculta campos innecesarios en móvil
        - Añade botones de acción rápida
        - Incluye impresión de albarán en formato ticket de 58mm como POS
        - Usa controlador web para generar HTML puro (no PDF)
    """,
    'author': 'Morato',
    'category': 'Sales',
    'depends': [
        'sale',
        'sale_management',
        'stock',
        'web',
        'partner_delivery_zone',
    ],
    'data': [
        'views/sale_order_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'morato_sale_order_mobile_custom/static/src/scss/sale_portal.scss',
            ]
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}
