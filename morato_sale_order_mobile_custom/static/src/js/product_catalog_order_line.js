/** @odoo-module **/

import { ProductCatalogOrderLine } from "@product/product_catalog/order_line/order_line";
import { patch } from "@web/core/utils/patch";
import { useState } from "@odoo/owl";

patch(ProductCatalogOrderLine.prototype, {
    setup() {
        super.setup();
        this.boxState = useState({
            boxes: 0,
            unitsPerBox: 1,
        });
    },

    get boxes() {
        return this.boxState.boxes;
    },

    get unitsPerBox() {
        return this.boxState.unitsPerBox;
    },

    decreaseBoxes() {
        if (this.boxState.boxes > 0) {
            this.boxState.boxes--;
            this.updateQuantityFromBoxes();
        }
    },

    increaseBoxes() {
        this.boxState.boxes++;
        this.updateQuantityFromBoxes();
    },

    setBoxes(ev) {
        const value = parseInt(ev.target.value) || 0;
        this.boxState.boxes = Math.max(0, value);
        this.updateQuantityFromBoxes();
    },

    setUnitsPerBox(ev) {
        const value = parseInt(ev.target.value) || 1;
        this.boxState.unitsPerBox = Math.max(1, value);
        this.updateQuantityFromBoxes();
    },

    updateQuantityFromBoxes() {
        const totalQuantity = this.boxState.boxes * this.boxState.unitsPerBox;
        if (totalQuantity > 0) {
            // Usar env.setQuantity que es el método correcto disponible en el contexto
            this.env.setQuantity({ target: { value: totalQuantity } });
        }
    },
});
