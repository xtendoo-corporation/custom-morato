from odoo import http
from odoo.http import request
import base64
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from io import BytesIO

class SaleOrderTicketController(http.Controller):

    @http.route('/sale_order/<int:order_id>/ticket', type='http', auth='user')
    def ticket_html(self, order_id):
        order = request.env['sale.order'].sudo().browse(order_id)
        return request.render('morato_sale_order_mobile_custom.sale_order_ticket_template', {
            'docs': [order],
        })

    @http.route('/sale_ticket/pdf/<int:order_id>', type='http', auth='user')
    def ticket_pdf(self, order_id):
        """Generar PDF del ticket de venta en formato 58mm con altura dinámica"""
        order = request.env['sale.order'].sudo().browse(order_id)

        if not order.exists():
            return request.not_found()

        # Crear buffer para el PDF
        buffer = BytesIO()

        # Configurar página para ticket de 58mm
        page_width = 58 * mm

        # Configurar fuente monoespaciada
        font_name = "Courier"
        font_size = 8
        line_height = 10
        margin = 2 * mm

        # Calcular altura necesaria dinámicamente
        base_lines = 8  # Título, pedido, cliente, fecha, total, mensaje final, espacios
        product_lines = len(order.order_line) * 2  # 2 líneas por producto (nombre + cantidad/precio)
        separators = 3  # Espacios adicionales y separadores

        total_lines = base_lines + product_lines + separators
        page_height = (total_lines * line_height) + (20 * mm)  # Margen superior e inferior

        # Altura mínima para evitar tickets muy pequeños
        min_height = 80 * mm
        page_height = max(page_height, min_height)

        # Crear canvas con altura dinámica
        p = canvas.Canvas(buffer, pagesize=(page_width, page_height))

        # Posición inicial
        y_position = page_height - 10 * mm

        def draw_text(text, y_pos, centered=False):
            if centered:
                text_width = p.stringWidth(text, font_name, font_size)
                x_pos = (page_width - text_width) / 2
            else:
                x_pos = margin
            p.drawString(x_pos, y_pos, text)
            return y_pos - line_height

        # Título
        p.setFont(font_name, font_size + 2)
        y_position = draw_text("*** PEDIDO DE VENTA ***", y_position)
        y_position -= 5

        # Información del pedido - centrada
        p.setFont(font_name, font_size)
        y_position = draw_text(f"Pedido: {order.name}", y_position)
        y_position = draw_text(f"Cliente: {order.partner_id.name}", y_position)
        y_position = draw_text(f"Fecha: {order.date_order.strftime('%d/%m/%Y %H:%M')}", y_position)
        y_position -= 5

        # Líneas del pedido - con formato de tabla
        if order.order_line:
            # Encabezado de tabla
            p.setFont(font_name, font_size - 1)
            header_y = y_position

            # Dibujar encabezados
            p.drawString(margin, header_y, "PRODUCTO")
            p.drawString(margin + 25*mm, header_y, "QTY")
            p.drawString(margin + 35*mm, header_y, "P.Ud")
            p.drawString(margin + 46*mm, header_y, "TOTAL")

            # Línea bajo los encabezados
            p.line(margin, header_y - 3, page_width - margin, header_y - 3)
            y_position = header_y - 8

            # Líneas de productos
            for line in order.order_line:
                p.setFont(font_name, font_size - 2)  # Fuente más pequeña para los datos

                # Columna 1: Producto - manejar nombres largos con múltiples líneas
                product_text = f"{line.product_id.name}"
                max_chars_per_line = 18  # Caracteres máximos por línea en la columna producto

                # Dividir el texto en líneas si es necesario
                product_lines = []
                words = product_text.split(' ')
                current_line = ""

                for word in words:
                    if len(current_line + word) <= max_chars_per_line:
                        current_line += word + " "
                    else:
                        if current_line:
                            product_lines.append(current_line.strip())
                        current_line = word + " "

                if current_line:
                    product_lines.append(current_line.strip())

                # Dibujar el nombre del producto (primera línea)
                first_line_y = y_position
                p.drawString(margin, first_line_y, product_lines[0] if product_lines else "")

                # Dibujar líneas adicionales del producto si las hay
                additional_lines_y = first_line_y
                for i, product_line in enumerate(product_lines[1:], 1):
                    additional_lines_y -= (line_height - 2)
                    p.drawString(margin, additional_lines_y, product_line)

                # Columna 2: Cantidad (alineada con la primera línea del producto)
                qty_text = f"{line.product_uom_qty}"
                qty_width = p.stringWidth(qty_text, font_name, font_size - 2)
                p.drawString(margin + 27*mm - qty_width/2, first_line_y, qty_text)

                # Columna 3: Precio unitario (alineada con la primera línea del producto)
                price_text = f"{line.price_unit:.2f}€"
                price_width = p.stringWidth(price_text, font_name, font_size - 2)
                p.drawString(margin + 38*mm - price_width/2, first_line_y, price_text)

                # Columna 4: Total (alineada con la primera línea del producto)
                subtotal = line.product_uom_qty * line.price_unit
                total_text = f"{subtotal:.2f}€"
                total_width = p.stringWidth(total_text, font_name, font_size - 2)
                p.drawString(page_width - margin - total_width, first_line_y, total_text)

                # Ajustar y_position según el número de líneas usadas para el producto
                lines_used = len(product_lines)
                y_position = first_line_y - (lines_used * (line_height - 2)) - 2

        # Línea separadora
        p.line(margin, y_position + 5, page_width - margin, y_position + 5)
        y_position -= 10

        # Total
        p.setFont(font_name, font_size + 1)
        y_position = draw_text(f"Total: {order.amount_total:.2f}€", y_position, centered=True)
        y_position -= 10

        # Mensaje final
        p.setFont(font_name, font_size)
        y_position = draw_text("Gracias por su compra", y_position, centered=True)

        # Finalizar PDF
        p.showPage()
        p.save()

        # Obtener el PDF como bytes
        pdf_data = buffer.getvalue()
        buffer.close()

        # Retornar respuesta con el PDF
        response = request.make_response(
            pdf_data,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', f'attachment; filename="Ticket de {order.name}.pdf"'),
            ]
        )

        return response

    # ===== CONTROLADORES PARA FACTURAS =====

    @http.route('/account_move/<int:invoice_id>/ticket', type='http', auth='user')
    def invoice_ticket_html(self, invoice_id):
        invoice = request.env['account.move'].sudo().browse(invoice_id)
        return request.render('morato_sale_order_mobile_custom.invoice_ticket_template', {
            'docs': [invoice],
        })

    @http.route('/invoice_ticket/pdf/<int:invoice_id>', type='http', auth='user')
    def invoice_ticket_pdf(self, invoice_id):
        """Generar PDF del ticket de factura en formato 58mm con altura dinámica"""
        invoice = request.env['account.move'].sudo().browse(invoice_id)

        if not invoice.exists():
            return request.not_found()

        # Crear buffer para el PDF
        buffer = BytesIO()

        # Configurar página para ticket de 58mm
        page_width = 58 * mm

        # Configurar fuente monoespaciada
        font_name = "Courier"
        font_size = 8
        line_height = 10
        margin = 2 * mm

        # Calcular altura necesaria dinámicamente con precisión optimizada
        base_lines = 6  # Título, factura, cliente, fecha, total, mensaje final (reducido)

        # Calcular líneas reales necesarias para cada producto
        total_product_lines = 0
        valid_product_lines = [line for line in invoice.invoice_line_ids
                              if (not line.display_type or line.display_type == 'product')
                              and line.name and line.name.strip()]

        for line in valid_product_lines:
            # Calcular cuántas líneas ocupará el nombre del producto
            product_text = f"{line.product_id.name if line.product_id else line.name}"
            max_chars_per_line = 18
            words = product_text.split(' ')
            current_line = ""
            lines_for_this_product = 0

            for word in words:
                if len(current_line + word) <= max_chars_per_line:
                    current_line += word + " "
                else:
                    if current_line:
                        lines_for_this_product += 1
                    current_line = word + " "

            if current_line:
                lines_for_this_product += 1

            # Cada producto usa las líneas calculadas
            total_product_lines += lines_for_this_product

        # Agregar líneas para encabezado de tabla si hay productos
        if valid_product_lines:
            total_product_lines += 2  # Encabezado + línea separadora

        # Espacios mínimos necesarios
        separators = 4  # Espacios entre secciones
        total_lines = base_lines + total_product_lines + separators

        # Calcular altura más ajustada
        page_height = (total_lines * line_height) + (20 * mm)  # Margen normal

        # Altura mínima más conservadora
        min_height = 80 * mm  # Reducido de 120mm
        page_height = max(page_height, min_height)

        # Para facturas con muchos productos, agregar un poco más de margen
        if len(valid_product_lines) > 5:
            page_height += 10 * mm  # Solo 10mm extra para facturas grandes

        # Crear canvas con altura dinámica
        p = canvas.Canvas(buffer, pagesize=(page_width, page_height))

        # Posición inicial
        y_position = page_height - 10 * mm

        def draw_text(text, y_pos, centered=False):
            if centered:
                text_width = p.stringWidth(text, font_name, font_size)
                x_pos = (page_width - text_width) / 2
            else:
                x_pos = margin
            p.drawString(x_pos, y_pos, text)
            return y_pos - line_height

        # Título
        p.setFont(font_name, font_size + 2)
        y_position = draw_text("*** FACTURA ***", y_position)
        y_position -= 5

        # Información de la factura - centrada
        p.setFont(font_name, font_size)
        y_position = draw_text(f"Factura: {invoice.name}", y_position)
        y_position = draw_text(f"Cliente: {invoice.partner_id.name}", y_position)
        y_position = draw_text(f"Fecha: {invoice.invoice_date.strftime('%d/%m/%Y') if invoice.invoice_date else 'N/A'}", y_position)
        y_position -= 5

        # Líneas de la factura - con formato de tabla
        product_lines_found = False
        if invoice.invoice_line_ids:
            # Filtrar líneas válidas - incluir display_type 'product'
            valid_lines = [line for line in invoice.invoice_line_ids
                          if (not line.display_type or line.display_type == 'product')
                          and line.name and line.name.strip()]

            if valid_lines:
                product_lines_found = True

                # Encabezado de tabla
                p.setFont(font_name, font_size - 1)
                header_y = y_position

                # Dibujar encabezados
                p.drawString(margin, header_y, "PRODUCTO")
                p.drawString(margin + 25*mm, header_y, "QTY")
                p.drawString(margin + 35*mm, header_y, "P.Ud")
                p.drawString(margin + 46*mm, header_y, "TOTAL")

                # Línea bajo los encabezados
                p.line(margin, header_y - 3, page_width - margin, header_y - 3)
                y_position = header_y - 8

                # Líneas de productos
                for line in valid_lines:
                    p.setFont(font_name, font_size - 2)  # Fuente más pequeña para los datos

                    # Columna 1: Producto - manejar nombres largos con múltiples líneas
                    product_text = f"{line.product_id.name if line.product_id else line.name}"
                    max_chars_per_line = 18  # Caracteres máximos por línea en la columna producto

                    # Dividir el texto en líneas si es necesario
                    product_lines = []
                    words = product_text.split(' ')
                    current_line = ""

                    for word in words:
                        if len(current_line + word) <= max_chars_per_line:
                            current_line += word + " "
                        else:
                            if current_line:
                                product_lines.append(current_line.strip())
                            current_line = word + " "

                    if current_line:
                        product_lines.append(current_line.strip())

                    # Dibujar el nombre del producto (primera línea)
                    first_line_y = y_position
                    p.drawString(margin, first_line_y, product_lines[0] if product_lines else "")

                    # Dibujar líneas adicionales del producto si las hay
                    additional_lines_y = first_line_y
                    for i, product_line in enumerate(product_lines[1:], 1):
                        additional_lines_y -= (line_height - 2)
                        p.drawString(margin, additional_lines_y, product_line)

                    # Columna 2: Cantidad (alineada con la primera línea del producto)
                    qty_text = f"{line.quantity or 0}"
                    qty_width = p.stringWidth(qty_text, font_name, font_size - 2)
                    p.drawString(margin + 27*mm - qty_width/2, first_line_y, qty_text)

                    # Columna 3: Precio unitario (alineada con la primera línea del producto)
                    price_text = f"{line.price_unit or 0:.2f}€"
                    price_width = p.stringWidth(price_text, font_name, font_size - 2)
                    p.drawString(margin + 38*mm - price_width/2, first_line_y, price_text)

                    # Columna 4: Total (alineada con la primera línea del producto)
                    subtotal = (line.quantity or 0) * (line.price_unit or 0)
                    total_text = f"{subtotal:.2f}€"
                    total_width = p.stringWidth(total_text, font_name, font_size - 2)
                    p.drawString(page_width - margin - total_width, first_line_y, total_text)

                    # Ajustar y_position según el número de líneas usadas para el producto
                    lines_used = len(product_lines)
                    y_position = first_line_y - (lines_used * (line_height - 2)) - 2

        # Si no se encontraron líneas de productos, mostrar mensaje
        if not product_lines_found:
            y_position = draw_text("No hay productos en esta factura", y_position, centered=True)
            y_position -= 2

        # Línea separadora
        p.line(margin, y_position + 5, page_width - margin, y_position + 5)
        y_position -= 10

        # Total
        p.setFont(font_name, font_size + 1)
        y_position = draw_text(f"Total: {invoice.amount_total:.2f}€", y_position, centered=True)
        y_position -= 10

        # Mensaje final
        p.setFont(font_name, font_size)
        y_position = draw_text("Gracias por su compra", y_position, centered=True)

        # Finalizar PDF
        p.showPage()
        p.save()

        # Obtener el PDF como bytes
        pdf_data = buffer.getvalue()
        buffer.close()

        # Retornar respuesta con el PDF
        response = request.make_response(
            pdf_data,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', f'attachment; filename="Ticket de {invoice.name}.pdf"'),
            ]
        )

        return response
