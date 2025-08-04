/** @odoo-module **/

import { Component, useState, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class InvoiceTicketWidget extends Component {
    setup() {
        this.state = useState({ docs: null });
        console.log("Props al montar componente de factura:", this.props);
        onMounted(() => this.renderTicket());
        console.log("Contexto en env:", this.env.context);
        console.log("Props recibidos en factura:", this.props);
    }

    async renderTicket() {
        const invoice_id = this.props.action?.context?.invoice_id;

        console.log("Invoice ID recibido:", invoice_id);

        if (!invoice_id) {
            console.warn("No se ha recibido invoice_id.");
            return;
        }

        const [invoice] = await rpc("/web/dataset/call_kw", {
            model: "account.move",
            method: "read",
            args: [[invoice_id]],
            kwargs: {
                fields: ["name", "partner_id", "invoice_date", "invoice_line_ids", "amount_total", "move_type"],
            },
        });

        console.log("Factura leída:", invoice);

        // Leer todas las líneas de factura primero
        const all_invoice_lines = await rpc("/web/dataset/call_kw", {
            model: "account.move.line",
            method: "read",
            args: [invoice.invoice_line_ids],
            kwargs: {
                fields: ["product_id", "name", "quantity", "price_unit", "price_subtotal", "display_type", "account_id"],
            },
        });

        console.log("Todas las líneas de factura leídas:", all_invoice_lines);

        // Analizar cada línea para depuración
        all_invoice_lines.forEach((line, index) => {
            console.log(`Línea ${index}:`, {
                name: line.name,
                product_id: line.product_id,
                quantity: line.quantity,
                display_type: line.display_type,
                price_unit: line.price_unit
            });
        });

        // Filtrar solo las líneas de productos - corregir la lógica de display_type
        const product_lines = all_invoice_lines.filter(line => {
            // En Odoo, display_type 'product' significa que ES un producto válido
            // Solo excluir 'line_section' y 'line_note'
            const isValidProduct = !line.display_type || line.display_type === 'product';
            const hasContent = line.name && line.name.trim() !== '';

            console.log(`Evaluando línea "${line.name}":`, {
                display_type: line.display_type,
                quantity: line.quantity,
                price_unit: line.price_unit,
                product_id: line.product_id,
                isValidProduct,
                hasContent,
                willInclude: isValidProduct && hasContent
            });

            return isValidProduct && hasContent;
        });

        console.log("Líneas de productos filtradas:", product_lines);

        invoice.invoice_line_ids = product_lines;
        this.state.docs = [invoice];

        console.log("Estado actualizado con docs de factura:", this.state.docs);

        // Generar PDF automáticamente después de cargar los datos
        setTimeout(() => this.generatePDF(), 500);
    }

    async generatePDF() {
        console.log("Generando PDF del ticket de factura...");

        try {
            const invoice_id = this.props.action?.context?.invoice_id;

            // Llamar al controlador para generar el PDF
            const response = await fetch(`/invoice_ticket/pdf/${invoice_id}`, {
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

                console.log("PDF de factura descargado exitosamente");

                // Cerrar la ventana automáticamente después de la descarga
                setTimeout(() => {
                    if (this.env.services && this.env.services.action) {
                        this.env.services.action.doAction({ type: 'ir.actions.act_window_close' });
                    }
                }, 500);

            } else {
                console.error("Error al generar PDF de factura:", response.statusText);
                // Fallback a impresión normal si falla
                this.onPrint();
            }
        } catch (error) {
            console.error("Error al generar PDF de factura:", error);
            // Fallback a impresión normal si falla
            this.onPrint();
        }
    }

    onPrint() {
        console.log("Llamada a imprimir ticket de factura");

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
                <title>Ticket de Factura</title>
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

InvoiceTicketWidget.template = "morato_sale_order_mobile_custom.invoice_ticket_template";
InvoiceTicketWidget.props = {
    action: { type: Object, optional: true },
    actionId: { type: Number, optional: true },
    updateActionState: { type: Function, optional: true },
    invoice_id: { type: Number, optional: true }
};
registry.category("actions").add("invoice_ticket_pos", InvoiceTicketWidget);
