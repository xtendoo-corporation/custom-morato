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
        y_position = draw_text("*** TICKET DE VENTA ***", y_position)
        y_position -= 5

        # Información del pedido - centrada
        p.setFont(font_name, font_size)
        y_position = draw_text(f"Pedido: {order.name}", y_position)
        y_position = draw_text(f"Cliente: {order.partner_id.name}", y_position)
        y_position = draw_text(f"Fecha: {order.date_order.strftime('%d/%m/%Y %H:%M')}", y_position)
        y_position -= 5

        # Líneas del pedido - SIN centrar
        for line in order.order_line:
            product_text = f"{line.product_id.name}"
            if len(product_text) > 20:
                product_text = product_text[:17] + "..."

            # Calcular subtotal (cantidad × precio unitario)
            subtotal = line.product_uom_qty * line.price_unit
            qty_price_text = f"x{line.product_uom_qty} {line.price_unit:.2f}€ = {subtotal:.2f}€"

            y_position = draw_text(product_text, y_position)
            y_position = draw_text(qty_price_text, y_position)
            y_position -= 2

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
