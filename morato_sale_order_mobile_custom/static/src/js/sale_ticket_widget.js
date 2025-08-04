/** @odoo-module **/

import { Component, useState, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class SaleTicketWidget extends Component {
    setup() {
        this.state = useState({ docs: null });
        console.log("Props al montar componente:", this.props);
        onMounted(() => this.renderTicket());
        console.log("Contexto en env:", this.env.context);
        console.log("Props recibidos:", this.props);
    }

    async renderTicket() {
        const order_id = this.props.action?.context?.order_id;

        console.log("Order ID recibido:", order_id);

        if (!order_id) {
            console.warn("No se ha recibido order_id.");
            return;
        }

        const [order] = await rpc("/web/dataset/call_kw", {
            model: "sale.order",
            method: "read",
            args: [[order_id]],
            kwargs: {
                fields: ["name", "partner_id", "date_order", "order_line", "amount_total"],
            },
        });

        console.log("Pedido leído:", order);

        const order_lines = await rpc("/web/dataset/call_kw", {
            model: "sale.order.line",
            method: "read",
            args: [order.order_line],
            kwargs: {
                fields: ["product_id", "product_uom_qty", "price_unit", "price_subtotal"],
            },
        });

        console.log("Líneas de pedido leídas:", order_lines);

        order.order_line = order_lines;
        this.state.docs = [order];

        console.log("Estado actualizado con docs:", this.state.docs);

        // Generar PDF automáticamente después de cargar los datos
        setTimeout(() => this.generatePDF(), 500);
    }

    async generatePDF() {
        console.log("Generando PDF del ticket...");

        try {
            const order_id = this.props.action?.context?.order_id;

            // Llamar al controlador para generar el PDF
            const response = await fetch(`/sale_ticket/pdf/${order_id}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (response.ok) {
                const blob = await response.blob();

                // Crear enlace de descarga automática sin mostrar ventanas
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `Ticket de ${this.state.docs[0].name}.pdf`;
                a.style.display = 'none'; // Ocultar el enlace
                document.body.appendChild(a);
                a.click();

                // Limpiar inmediatamente
                setTimeout(() => {
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                }, 100);

                console.log("PDF descargado exitosamente");

                // Cerrar la ventana automáticamente después de la descarga
                setTimeout(() => {
                    if (this.env.services && this.env.services.action) {
                        this.env.services.action.doAction({ type: 'ir.actions.act_window_close' });
                    }
                }, 500);

            } else {
                console.error("Error al generar PDF:", response.statusText);
                // Fallback a impresión normal si falla
                this.onPrint();
            }
        } catch (error) {
            console.error("Error al generar PDF:", error);
            // Fallback a impresión normal si falla
            this.onPrint();
        }
    }

    onPrint() {
        console.log("Llamada a imprimir ticket");

        // Obtener el contenido del ticket
        const ticketContent = this.el.querySelector('div[style*="width: 58mm"]');

        if (!ticketContent) {
            console.warn("No se encontró el contenido del ticket para imprimir");
            return;
        }

        // Crear una nueva ventana para la impresión
        const printWindow = window.open('', '_blank', 'width=300,height=600');

        // Escribir el contenido HTML para la impresión
        printWindow.document.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>Ticket de Venta</title>
                <style>
                    @page {
                        margin: 0;
                        size: 58mm auto;
                    }
                    body {
                        margin: 0;
                        padding: 5mm;
                        font-family: 'Courier New', monospace;
                        font-size: 12px;
                        line-height: 1.2;
                    }
                    @media print {
                        body {
                            width: 48mm;
                        }
                    }
                </style>
            </head>
            <body>
                ${ticketContent.innerHTML}
            </body>
            </html>
        `);

        printWindow.document.close();

        // Esperar un momento para que el contenido se cargue y luego imprimir
        setTimeout(() => {
            printWindow.print();
            printWindow.close();
        }, 250);
    }
}

SaleTicketWidget.template = "morato_sale_order_mobile_custom.sale_order_ticket_template";
SaleTicketWidget.props = {
    action: { type: Object, optional: true },
    actionId: { type: Number, optional: true },
    updateActionState: { type: Function, optional: true },
    order_id: { type: Number, optional: true }
};
registry.category("actions").add("sale_ticket_pos", SaleTicketWidget);
