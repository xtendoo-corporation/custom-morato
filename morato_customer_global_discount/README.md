# Morato Customer Global Discount

## Descripción

Este módulo permite establecer un porcentaje de descuento global en los registros de clientes. Cuando se confirma un pedido de venta o se publica una factura, el porcentaje de descuento global del cliente se aplica automáticamente utilizando la lógica estándar de descuentos de Odoo.

## Funcionalidades

- **Campo de descuento global**: Añade un campo "Descuento Global (%)" en la ficha del cliente
- **Descuento automático en pedidos**: Aplica automáticamente el descuento cuando se confirma un pedido de venta usando el wizard estándar de Odoo `sale.order.discount`
- **Descuento automático en facturas**: Aplica automáticamente el descuento cuando se publica una factura usando lógica similar al estándar de Odoo
- **Uso del producto estándar**: Utiliza el producto de descuento configurado en la compañía (`company.sale_discount_product_id`)
- **Manejo de impuestos**: Agrupa las líneas por impuestos y maneja correctamente los impuestos fijos (no descontables)
- **Integración nativa**: Usa la misma lógica que el botón "Descuento" estándar de Odoo pero de forma automática

## Instalación

1. Copiar el módulo en el directorio de addons
2. Actualizar la lista de aplicaciones
3. Instalar el módulo "Morato Customer Global Discount"

## Uso

1. **Configurar descuento en cliente**:
   - Ir a Contactos > Clientes
   - Abrir la ficha de un cliente
   - En la pestaña "Ventas y Compras", configurar el campo "Descuento Global (%)"

2. **Aplicación automática**:
   - El descuento se aplica automáticamente al confirmar pedidos de venta
   - El descuento se aplica automáticamente al publicar facturas de venta
   - Se crea una línea adicional con el descuento aplicado usando la lógica estándar de Odoo

## Notas técnicas

### Lógica de descuentos en pedidos de venta:
- Utiliza el wizard estándar `sale.order.discount` con tipo `'so_discount'` (Descuento Global)
- Llama al método `action_apply_discount()` del wizard estándar de Odoo
- Respeta la configuración de producto de descuento de la compañía

### Lógica de descuentos en facturas:
- Implementa lógica similar al wizard estándar para facturas
- Agrupa líneas por impuestos para manejar correctamente diferentes tipos de IVA
- Excluye impuestos fijos del cálculo de descuento
- Usa el producto de descuento configurado en la compañía

### Producto de descuento:
- Si la compañía ya tiene configurado un producto de descuento (`sale_discount_product_id`), lo utiliza
- Si no existe, crea automáticamente uno siguiendo las especificaciones estándar de Odoo
- El producto creado se configura automáticamente como producto de descuento de la compañía

### Manejo de impuestos:
- Agrupa las líneas por impuestos para crear líneas de descuento apropiadas
- Los impuestos fijos no se incluyen en el cálculo del descuento
- Crea líneas de descuento separadas para diferentes grupos de impuestos

## Compatibilidad

- **Odoo 18.0**: Totalmente compatible
- **Wizard estándar**: Utiliza la misma lógica que el wizard `sale.order.discount` nativo de Odoo
- **Configuración de compañía**: Respeta la configuración del producto de descuento de la compañía

## Autor

Xtendoo Software SLU
Website: https://www.xtendoo.es

## Licencia

LGPL-3
