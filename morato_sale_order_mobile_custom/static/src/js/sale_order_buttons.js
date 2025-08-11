/** @odoo-module **/

import { registry } from "@web/core/registry";
import { FormView } from "@web/views/form/form_view";
import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";

/**
 * Extendemos el FormController para añadir métodos necesarios
 * para los botones personalizados
 */
patch(FormController.prototype, {
    /**
     * Verifica si estamos en un formulario de pedido de venta
     */
    isSaleOrder() {
        return this.model?.root?.resModel === 'sale.order';
    },

    /**
     * Verifica si el pedido está confirmado
     */
    isOrderConfirmed() {
        if (!this.isSaleOrder()) return false;
        const state = this.model.root.data.state;
        return state === 'sale' || state === 'done';
    },

    /**
     * Verifica si el pedido tiene facturas
     */
    hasInvoices() {
        if (!this.isSaleOrder()) return false;
        return this.model.root.data.invoice_ids?.length > 0;
    },

    /**
     * Acción para ver el ticket de venta
     */
    onViewTicket() {
        if (!this.isSaleOrder()) return;

        this.env.services.action.doAction({
            type: 'ir.actions.client',
            tag: 'sale_ticket_pos',
            target: 'new',
            context: {'order_id': this.model.root.resId}
        });
    },

    /**
     * Acción para ver la factura
     */
    onViewInvoice() {
        if (!this.isSaleOrder()) return;

        this.env.services.action.doAction({
            type: 'object',
            name: 'action_view_invoice',
            resModel: 'sale.order',
            resId: this.model.root.resId
        });
    }
});

/**
 * Registramos un componente que irá como botón en la barra de herramientas
 * superior de los pedidos de venta
 */
const formStatusBarButtons = {
    template: "morato_sale_order_mobile_custom.SaleOrderButtons",

    setup() {
        this.controller = this.env.controller;
    }
};

// Registramos nuestra plantilla como botones de formulario
registry.category("view_widgets").add("sale_order_buttons", formStatusBarButtons);
