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

        # Obtener información de la empresa
        company = order.company_id or request.env.company

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
        # Añadir líneas para la información de la empresa
        company_lines = 5  # Nombre, dirección, NIF, teléfono, etc.
        base_lines = 8  # Título, pedido, cliente, fecha, total, mensaje final, espacios
        product_lines = len(order.order_line) * 2  # 2 líneas por producto (nombre + cantidad/precio)
        separators = 4  # Espacios adicionales y separadores (uno más para separar la info de empresa)

        total_lines = company_lines + base_lines + product_lines + separators
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

        # Información de la empresa - centrada
        p.setFont(font_name, font_size + 1)
        y_position = draw_text(company.name, y_position, centered=True)

        p.setFont(font_name, font_size)
        if company.street:
            y_position = draw_text(company.street, y_position, centered=True)
        if company.zip or company.city:
            address = ""
            if company.zip:
                address += company.zip
            if company.city:
                address += " " + company.city
            y_position = draw_text(address.strip(), y_position, centered=True)
        if company.vat:
            y_position = draw_text(f"NIF: {company.vat}", y_position, centered=True)
        if company.phone:
            y_position = draw_text(f"Tel: {company.phone}", y_position, centered=True)

        # Separador después de la información de empresa
        y_position -= 5
        p.line(margin, y_position + 3, page_width - margin, y_position + 3)
        y_position -= 5

        # Título
        # p.setFont(font_name, font_size + 2)
        # y_position = draw_text("*** PEDIDO DE VENTA ***", y_position)
        y_position -= 5

        # Información del pedido - centrada
        p.setFont(font_name, font_size)
        y_position = draw_text(f"Pedido: {order.name}", y_position)
        y_position = draw_text(f"Cliente: {order.partner_id.name}", y_position)
        y_position = draw_text(f"Fecha: {order.date_order.strftime('%d/%m/%Y %H:%M')}", y_position)
        y_position -= 5

        # Líneas del pedido - con formato de tabla
        if order.order_line:
            # Ya no necesitamos encabezados de tabla para el nuevo formato
            y_position -= 5  # Espacio antes de comenzar con los productos

            # Líneas de productos con nuevo formato de dos columnas
            for line in order.order_line:
                p.setFont(font_name, font_size - 1)  # Fuente para el nombre del producto

                # Columna 1: Producto - manejar nombres largos con múltiples líneas
                product_text = f"{line.product_id.name}"
                max_chars_per_line = 30  # Caracteres máximos por línea para el nombre

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

                # Dibujar el nombre del producto
                first_line_y = y_position
                for i, product_line in enumerate(product_lines):
                    if i == 0:
                        p.drawString(margin, first_line_y, product_line)
                    else:
                        first_line_y -= (line_height - 2)
                        p.drawString(margin, first_line_y, product_line)

                # Precio total a la derecha (alineado con la primera línea del producto)
                p.setFont(font_name, font_size)
                subtotal = line.product_uom_qty * line.price_unit
                total_text = f"{subtotal:.2f}€"
                total_width = p.stringWidth(total_text, font_name, font_size)
                p.drawString(page_width - margin - total_width, y_position, total_text)

                # Cantidad x Precio debajo del nombre del producto
                qty_price_text = f"{line.product_uom_qty} x {line.price_unit:.2f}€"
                qty_price_y = first_line_y - (line_height - 2)
                p.setFont(font_name, font_size - 2)
                p.drawString(margin + 2, qty_price_y, qty_price_text)

                # Calcular la posición Y para el próximo producto
                # Consideramos el espacio usado por el nombre + la línea de cantidad/precio + espacio adicional
                lines_used = len(product_lines)
                y_position = qty_price_y - (line_height)  # Espacio después de cada producto

        # Línea separadora
        p.line(margin, y_position + 5, page_width - margin, y_position + 5)
        y_position -= 10

        # Información del IVA - centrada como el total
        p.setFont(font_name, font_size)

        # Base imponible
        base_text = f"Base imponible: {order.amount_untaxed:.2f}€"
        y_position = draw_text(base_text, y_position, centered=True)

        # Agrupar impuestos por tipo de IVA para mostrarlos más compactamente
        tax_groups = {}
        for line in order.order_line:
            for tax in line.tax_id:
                tax_amount = line.price_subtotal * (tax.amount / 100)
                if tax.amount in tax_groups:
                    tax_groups[tax.amount] += tax_amount
                else:
                    tax_groups[tax.amount] = tax_amount

        # Mostrar cada tipo de IVA
        for tax_rate, tax_amount in tax_groups.items():
            tax_text = f"IVA {tax_rate}%: {tax_amount:.2f}€"
            y_position = draw_text(tax_text, y_position, centered=True)

        # Espacio adicional antes del total
        y_position -= 2

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

        # Obtener información de la empresa
        company = invoice.company_id or request.env.company

        # Crear buffer para el PDF
        buffer = BytesIO()

        # Configurar página para ticket de 58mm
        page_width = 58 * mm

        # Configurar fuente monoespaciada
        font_name = "Courier"
        font_size = 8
        line_height = 10
        margin = 2 * mm

        # Filtrar líneas de producto válidas
        valid_product_lines = [line for line in invoice.invoice_line_ids
                              if (not line.display_type or line.display_type == 'product')
                              and line.name and line.name.strip()]

        # Calcular altura necesaria dinámicamente - usando estructura igual al ticket de venta
        company_lines = 5  # Nombre, dirección, NIF, teléfono, etc.
        base_lines = 8  # Título, factura, cliente, fecha, total, mensaje final
        product_lines = len(valid_product_lines) * 2  # 2 líneas por producto (nombre + cantidad/precio)
        separators = 4  # Espacios adicionales y separadores
        tax_lines = 3  # Base imponible + líneas de IVA

        total_lines = company_lines + base_lines + product_lines + separators + tax_lines
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

        # Información de la empresa - centrada
        p.setFont(font_name, font_size + 1)
        y_position = draw_text(company.name, y_position, centered=True)

        p.setFont(font_name, font_size)
        if company.street:
            y_position = draw_text(company.street, y_position, centered=True)
        if company.zip or company.city:
            address = ""
            if company.zip:
                address += company.zip
            if company.city:
                address += " " + company.city
            y_position = draw_text(address.strip(), y_position, centered=True)
        if company.vat:
            y_position = draw_text(f"NIF: {company.vat}", y_position, centered=True)
        if company.phone:
            y_position = draw_text(f"Tel: {company.phone}", y_position, centered=True)

        # Separador después de la información de empresa
        y_position -= 5
        p.line(margin, y_position + 3, page_width - margin, y_position + 3)
        y_position -= 5

        # Título
        # p.setFont(font_name, font_size + 2)
        # y_position = draw_text("*** FACTURA ***", y_position)
        y_position -= 5

        # Información de la factura - centrada
        p.setFont(font_name, font_size)
        y_position = draw_text(f"Factura: {invoice.name}", y_position)
        y_position = draw_text(f"Cliente: {invoice.partner_id.name}", y_position)
        y_position = draw_text(f"Fecha: {invoice.invoice_date.strftime('%d/%m/%Y') if invoice.invoice_date else 'N/A'}", y_position)
        y_position -= 5

        # Líneas de la factura - con formato de dos columnas
        if valid_product_lines:
            y_position -= 5  # Espacio antes de comenzar con los productos

            # Líneas de productos con nuevo formato de dos columnas
            for line in valid_product_lines:
                p.setFont(font_name, font_size - 1)  # Fuente para el nombre del producto

                # Columna 1: Producto - manejar nombres largos con múltiples líneas
                product_text = f"{line.product_id.name if line.product_id else line.name}"
                max_chars_per_line = 30  # Caracteres máximos por línea para el nombre

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

                # Dibujar el nombre del producto
                first_line_y = y_position
                for i, product_line in enumerate(product_lines):
                    if i == 0:
                        p.drawString(margin, first_line_y, product_line)
                    else:
                        first_line_y -= (line_height - 2)
                        p.drawString(margin, first_line_y, product_line)

                # Precio total a la derecha (alineado con la primera línea del producto)
                p.setFont(font_name, font_size)
                subtotal = (line.quantity or 0) * (line.price_unit or 0)
                total_text = f"{subtotal:.2f}€"
                total_width = p.stringWidth(total_text, font_name, font_size)
                p.drawString(page_width - margin - total_width, y_position, total_text)

                # Cantidad x Precio debajo del nombre del producto
                qty_price_text = f"{line.quantity or 0} x {line.price_unit or 0:.2f}€"
                qty_price_y = first_line_y - (line_height - 2)
                p.setFont(font_name, font_size - 2)
                p.drawString(margin + 2, qty_price_y, qty_price_text)

                # Calcular la posición Y para el próximo producto
                # Consideramos el espacio usado por el nombre + la línea de cantidad/precio + espacio adicional
                lines_used = len(product_lines)
                y_position = qty_price_y - (line_height)  # Espacio después de cada producto

        # Si no se encontraron líneas de productos, mostrar mensaje
        if not valid_product_lines:
            y_position = draw_text("No hay productos en esta factura", y_position, centered=True)
            y_position -= 2

        # Línea separadora
        p.line(margin, y_position + 5, page_width - margin, y_position + 5)
        y_position -= 10

        # Información del IVA - centrada como el total
        p.setFont(font_name, font_size)

        # Base imponible
        base_text = f"Base imponible: {invoice.amount_untaxed:.2f}€"
        y_position = draw_text(base_text, y_position, centered=True)

        # Agrupar impuestos por tipo de IVA
        tax_groups = {}

        # En Odoo 18, tax_line_ids ya no existe, usamos la estructura actual
        for line in valid_product_lines:
            for tax in line.tax_ids:
                tax_rate = tax.amount
                tax_amount = line.price_subtotal * (tax_rate / 100)
                if tax_rate in tax_groups:
                    tax_groups[tax_rate] += tax_amount
                else:
                    tax_groups[tax_rate] = tax_amount

        # Mostrar cada tipo de IVA
        for tax_rate, tax_amount in tax_groups.items():
            tax_text = f"IVA {tax_rate}%: {tax_amount:.2f}€"
            y_position = draw_text(tax_text, y_position, centered=True)

        # Espacio adicional antes del total
        y_position -= 2

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

        # Generar respuesta exactamente igual que el ticket de venta
        response = request.make_response(
            pdf_data,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', f'attachment; filename="Ticket de {invoice.name}.pdf"'),
            ]
        )

        return response
