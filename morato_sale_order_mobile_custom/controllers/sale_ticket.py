from odoo import http
from odoo.http import request
import base64
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from io import BytesIO
import os
from reportlab.lib.utils import ImageReader

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
        font_size = 9
        line_height = 11
        margin = 1 * mm

        # Función auxiliar para formatear números con coma decimal
        def format_decimal(value):
            return f"{value:.2f}".replace(".", ",")

        # Función auxiliar para contar líneas reales de texto
        def count_text_lines(text, max_width, temp_canvas):
            if not text:
                return 1
            avg_char_width = temp_canvas.stringWidth("m", font_name, font_size)
            max_chars_per_line = int(max_width / avg_char_width) - 2
            words = text.split(' ')
            lines = 0
            current_line = ""
            for word in words:
                if len(current_line + word) <= max_chars_per_line:
                    current_line += word + " "
                else:
                    if current_line:
                        lines += 1
                    current_line = word + " "
            if current_line:
                lines += 1
            return max(lines, 1)

        # Crear canvas temporal para calculos
        temp_buffer = BytesIO()
        temp_canvas = canvas.Canvas(temp_buffer, pagesize=(page_width, 100 * mm))
        temp_canvas.setFont(font_name, font_size)

        # Calcular altura necesaria dinámicamente
        company_lines = 5
        base_lines = 8
        separators = 6  # Aumentar separadores

        # Calcular líneas reales del cliente
        cliente_name = order.partner_id.name or ''
        max_cliente_width = page_width - 2 * margin - temp_canvas.stringWidth("Cliente: ", font_name, font_size)
        cliente_extra_lines = count_text_lines(cliente_name, max_cliente_width, temp_canvas) - 1

        # Calcular líneas reales de productos
        product_lines = 0
        if order.order_line:
            text_width = page_width - (2 * margin) - (13 * mm)  # Espacio para precio
            for line in order.order_line:
                product_name = line.product_id.name or ""
                name_lines = count_text_lines(product_name, text_width, temp_canvas)
                product_lines += name_lines + 1  # +1 para la línea de cantidad/precio

        total_lines = company_lines + base_lines + product_lines + separators + cliente_extra_lines
        page_height = (total_lines * line_height) + (3 * mm)  # Más margen de seguridad

        # Altura mínima y máxima
        min_height = 120 * mm
        max_height = 600 * mm  # Límite máximo de seguridad
        page_height = max(min_height, min(page_height, max_height))

        # Crear canvas definitivo con altura calculada
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
        if company.mobile:
            y_position = draw_text(f"Móvil: {company.mobile}", y_position, centered=True)
        if company.vat:
            y_position = draw_text(f"NIF: {company.vat}", y_position, centered=True)

        # Separador después de la información de empresa
        y_position -= 5
        p.line(margin, y_position + 3, page_width - margin, y_position + 3)
        y_position -= 5

        # Información del pedido
        p.setFont(font_name, font_size)
        cliente_label = f"Cliente: "
        cliente_name = order.partner_id.name or ''
        max_cliente_width = page_width - 2 * margin - p.stringWidth(cliente_label, font_name, font_size)
        cliente_lines = []
        if p.stringWidth(cliente_name, font_name, font_size) > max_cliente_width:
            words = cliente_name.split(' ')
            current_line = ''
            for word in words:
                if p.stringWidth(current_line + word + ' ', font_name, font_size) <= max_cliente_width:
                    current_line += word + ' '
                else:
                    if current_line:
                        cliente_lines.append(current_line.strip())
                    current_line = word + ' '
            if current_line:
                cliente_lines.append(current_line.strip())
        else:
            cliente_lines = [cliente_name]

        y_position = draw_text(f"Pedido", y_position)
        y_position = draw_text(f"{cliente_label}{cliente_lines[0]}", y_position)
        for extra_line in cliente_lines[1:]:
            y_position = draw_text(f"{extra_line}", y_position)
        y_position = draw_text(f"Fecha: {order.date_order.strftime('%d/%m/%Y %H:%M')}", y_position)
        y_position -= 5
        p.line(margin, y_position + 3, page_width - margin, y_position + 3)
        y_position -= 5

        # Líneas del pedido
        if order.order_line:
            y_position -= 5
            price_width = 13 * mm
            for line in order.order_line:
                p.setFont(font_name, font_size)
                product_text = f"{line.product_id.name}"
                text_width = page_width - (2 * margin) - price_width
                avg_char_width = p.stringWidth("m", font_name, font_size)
                max_chars_per_line = int(text_width / avg_char_width) - 2
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

                first_line_y = y_position
                for i, product_line in enumerate(product_lines):
                    if i == 0:
                        p.drawString(margin, first_line_y, product_line)
                    else:
                        first_line_y -= (line_height - 1)
                        p.drawString(margin, first_line_y, product_line)

                qty = line.product_uom_qty if hasattr(line, 'product_uom_qty') else line.quantity
                line_total = getattr(line, 'price_total', None)
                price_unit_real = line.price_unit
                qty_text = int(qty) if qty == int(qty) else str(qty).replace('.', ',')
                price_unit_text = str(f"{price_unit_real:.2f}").replace('.', ',')
                qty_price_text = f"{qty_text} x {price_unit_text}€"
                if hasattr(line, 'discount') and line.discount:
                    qty_price_text += f"  (-{format_decimal(line.discount)}%)"
                qty_price_y = first_line_y - (line_height - 1)
                p.setFont(font_name, font_size)
                p.drawString(margin, qty_price_y, qty_price_text)

                if line_total is not None:
                    total_text = f"{format_decimal(line_total)}€"
                else:
                    total_text = f"{format_decimal(qty * price_unit_real)}€"
                total_width = p.stringWidth(total_text, font_name, font_size)
                p.drawString(page_width - margin - total_width, y_position, total_text)
                y_position = qty_price_y - line_height

        # Línea separadora
        p.line(margin, y_position + 5, page_width - margin, y_position + 5)
        y_position -= 10

        # Total alineado a la derecha
        total_text = f"Total: {format_decimal(order.amount_total)}€"
        total_width = p.stringWidth(total_text, font_name, font_size + 2)
        p.setFont(font_name, font_size + 2)
        p.drawString(page_width - margin - total_width, y_position, total_text)
        y_position -= 15

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

        # Configurar fuente monoespaciada igual que en ticket de venta
        font_name = "Courier"
        font_size = 9
        line_height = 11
        margin = 1 * mm

        # Función auxiliar para formatear números con coma decimal
        def format_decimal(value):
            return f"{value:.2f}".replace(".", ",")

        # Función auxiliar para contar líneas reales de texto
        def count_text_lines(text, max_width, temp_canvas):
            if not text:
                return 1
            avg_char_width = temp_canvas.stringWidth("m", font_name, font_size)
            max_chars_per_line = int(max_width / avg_char_width) - 2
            words = text.split(' ')
            lines = 0
            current_line = ""
            for word in words:
                if len(current_line + word) <= max_chars_per_line:
                    current_line += word + " "
                else:
                    if current_line:
                        lines += 1
                    current_line = word + " "
            if current_line:
                lines += 1
            return max(lines, 1)

        # Obtener el cliente (partner)
        partner = invoice.partner_id

        # Filtrar líneas de producto válidas
        valid_product_lines = [line for line in invoice.invoice_line_ids
                               if (not line.display_type or line.display_type == 'product')
                               and line.name and line.name.strip()]

        # Crear canvas temporal para cálculos
        temp_buffer = BytesIO()
        temp_canvas = canvas.Canvas(temp_buffer, pagesize=(page_width, 100 * mm))
        temp_canvas.setFont(font_name, font_size)

        # Calcular altura necesaria dinámicamente
        company_lines = 5
        base_lines = 10  # Ajustado para incluir datos del cliente
        separators = 6
        tax_lines = 4  # Base imponible + líneas de IVA + total
        bank_lines = 3  # Cuenta bancaria

        # Calcular líneas reales del cliente
        if partner.name:
            max_cliente_width = page_width - 2 * margin
            cliente_extra_lines = count_text_lines(partner.name, max_cliente_width, temp_canvas) - 1
            # Agregar líneas adicionales para otros datos del cliente (NIF, dirección, etc.)
            cliente_extra_lines += 4  # NIF, dirección, población, teléfono
        else:
            cliente_extra_lines = 0

        # Calcular líneas reales de productos
        product_lines = 0
        if valid_product_lines:
            text_width = page_width - (2 * margin) - (13 * mm)  # Espacio para precio
            for line in valid_product_lines:
                product_name = line.product_id.name if line.product_id else line.name
                name_lines = count_text_lines(product_name or "", text_width, temp_canvas)
                product_lines += name_lines + 1  # +1 para la línea de cantidad/precio

        # Calcular líneas dinámicas de impuestos
        tax_groups = {}
        for line in valid_product_lines:
            for tax in line.tax_ids:
                tax_rate = tax.amount
                if tax_rate not in tax_groups:
                    tax_groups[tax_rate] = 0

        dynamic_tax_lines = len(tax_groups) + 2  # +2 para base imponible y total

        total_lines = company_lines + base_lines + product_lines + separators + dynamic_tax_lines + cliente_extra_lines + bank_lines
        page_height = (total_lines * line_height) + (2 * mm)  # Margen de seguridad

        # Altura mínima y máxima
        min_height = 120 * mm
        max_height = 600 * mm
        page_height = max(min_height, min(page_height, max_height))

        # Crear canvas definitivo con altura calculada
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
        if company.mobile:
            y_position = draw_text(f"Móvil: {company.mobile}", y_position, centered=True)
        if company.vat:
            y_position = draw_text(f"NIF: {company.vat}", y_position, centered=True)

        # Separador después de la información de empresa
        y_position -= 5
        p.line(margin, y_position + 3, page_width - margin, y_position + 3)
        y_position -= 5

        # Información de la factura
        p.setFont(font_name, font_size)
        if invoice.move_type == 'out_refund':
            y_position = draw_text("Factura Rectificativa", y_position)
            if not invoice.name and invoice.state == 'draft':
                y_position = draw_text("Borrador", y_position)
            else:
                y_position = draw_text(invoice.name or "", y_position)
        elif not invoice.name and invoice.state == 'draft':
            y_position = draw_text("Factura Borrador", y_position)
        else:
            y_position = draw_text(f"Factura: {invoice.name}", y_position)

        fecha_text = f"Fecha: {invoice.invoice_date.strftime('%d/%m/%Y') if invoice.invoice_date else 'N/A'}"
        y_position = draw_text(fecha_text, y_position)

        # Información del cliente
        y_position = draw_text("Cliente:", y_position)
        cliente_datos = []
        if partner.name:
            cliente_datos.append(partner.name)
        if partner.vat:
            cliente_datos.append(partner.vat)
        if partner.street:
            cliente_datos.append(partner.street)
        if partner.zip or partner.city:
            address = ""
            if partner.zip:
                address += partner.zip + " "
            if partner.city:
                address += partner.city
            cliente_datos.append(address.strip())
        if partner.phone:
            cliente_datos.append(partner.phone)

        # Dividir cada dato en varias líneas si es necesario
        for dato in cliente_datos:
            max_width = page_width - 2 * margin
            palabras = dato.split(' ')
            linea_actual = ""
            for palabra in palabras:
                test_line = (linea_actual + palabra + " ").strip()
                if p.stringWidth(test_line, font_name, font_size) <= max_width:
                    linea_actual = test_line + " "
                else:
                    if linea_actual:
                        y_position = draw_text(linea_actual.strip(), y_position)
                    linea_actual = palabra + " "
            if linea_actual:
                y_position = draw_text(linea_actual.strip(), y_position)

        # Separador entre los datos del cliente y los productos
        y_position -= 2
        p.line(margin, y_position + 3, page_width - margin, y_position + 3)
        y_position -= 3

        # Líneas de la factura
        if valid_product_lines:
            y_position -= 5
            price_width = 13 * mm

            for line in valid_product_lines:
                p.setFont(font_name, font_size)
                product_text = f"{line.product_id.name if line.product_id else line.name}"
                text_width = page_width - (2 * margin) - price_width
                avg_char_width = p.stringWidth("m", font_name, font_size)
                max_chars_per_line = int(text_width / avg_char_width) - 2

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
                        first_line_y -= (line_height - 1)
                        p.drawString(margin, first_line_y, product_line)

                # Precio total a la derecha
                p.setFont(font_name, font_size)
                subtotal = line.price_subtotal
                total_text = f"{format_decimal(subtotal)}€"
                total_width = p.stringWidth(total_text, font_name, font_size)
                p.drawString(page_width - margin - total_width, y_position, total_text)

                # Cantidad x Precio debajo del nombre del producto
                qty = line.quantity or 0
                subtotal = line.price_subtotal or 0

                if qty > 0:
                    effective_price = subtotal / qty
                else:
                    effective_price = 0

                qty_text = int(qty) if qty == int(qty) else format_decimal(qty)
                qty_price_text = f"{qty_text} x {format_decimal(effective_price)}€"

                if getattr(line, 'discount', 0):
                    qty_price_text += f"  (-{format_decimal(line.discount)}%)"

                qty_price_y = first_line_y - (line_height - 1)
                p.setFont(font_name, font_size)
                p.drawString(margin, qty_price_y, qty_price_text)

                y_position = qty_price_y - line_height

        # Si no se encontraron líneas de productos
        if not valid_product_lines:
            y_position = draw_text("No hay productos en esta factura", y_position, centered=True)
            y_position -= 2

        # Línea separadora
        p.line(margin, y_position + 5, page_width - margin, y_position + 5)
        y_position -= 10

        # Información del IVA - alineada a la derecha
        p.setFont(font_name, font_size)

        # Base imponible
        base_text = f"Base imponible: {format_decimal(invoice.amount_untaxed)}€"
        base_text_width = p.stringWidth(base_text, font_name, font_size)
        p.drawString(page_width - margin - base_text_width, y_position, base_text)
        y_position -= line_height

        # Agrupar impuestos por tipo de IVA
        tax_groups = {}
        base_groups = {}
        for line in valid_product_lines:
            line_base = line.price_subtotal or 0.0
            for tax in line.tax_ids:
                tax_rate = tax.amount
                tax_amount = line_base * (tax_rate / 100)
                if tax_rate in tax_groups:
                    tax_groups[tax_rate] += tax_amount
                    base_groups[tax_rate] += line_base
                else:
                    tax_groups[tax_rate] = tax_amount
                    base_groups[tax_rate] = line_base

        # Mostrar líneas de IVA
        for tax_rate in sorted(base_groups.keys()):
            base_val = format_decimal(base_groups[tax_rate])
            iva_val = format_decimal(tax_rate)
            tax_val = format_decimal(tax_groups.get(tax_rate, 0))
            base_text = f"{base_val}€ al {iva_val}%: {tax_val}€"
            base_text_width = p.stringWidth(base_text, font_name, font_size)
            p.drawString(page_width - margin - base_text_width, y_position, base_text)
            y_position -= line_height

        # Espacio adicional antes del total
        y_position -= 2

        # Total - alineado a la derecha pero con fuente más grande
        p.setFont(font_name, font_size + 2)
        total_text = f"Total: {format_decimal(invoice.amount_total)}€"
        total_text_width = p.stringWidth(total_text, font_name, font_size + 2)
        p.drawString(page_width - margin - total_text_width, y_position, total_text)

        # Espacio reducido debajo del total
        y_position -= 15

        # Mostrar número de cuenta bancaria de la compañía
        p.setFont(font_name, font_size)
        bank_account = request.env['res.partner.bank'].search([('partner_id', '=', company.partner_id.id)], limit=1)
        account_number = bank_account.acc_number if bank_account else None

        cuenta_label = "Cuenta bancaria:"
        p.drawString(margin, y_position, cuenta_label)
        y_position -= line_height

        if account_number:
            p.drawString((page_width - p.stringWidth(account_number, font_name, font_size)) / 2, y_position,
                         account_number)
        else:
            p.drawString((page_width - p.stringWidth("No disponible", font_name, font_size)) / 2, y_position,
                         "No disponible")

        # Finalizar PDF
        p.showPage()
        p.save()

        # Obtener el PDF como bytes
        pdf_data = buffer.getvalue()
        buffer.close()

        # Generar respuesta
        response = request.make_response(
            pdf_data,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', f'attachment; filename="Ticket de {invoice.name}.pdf"'),
            ]
        )

        return response
