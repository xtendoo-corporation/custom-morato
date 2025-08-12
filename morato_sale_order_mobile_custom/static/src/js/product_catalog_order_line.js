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

        // Intentar obtener el producto desde el env o parent
        this.initializeBoxUnits();
    },

    // Método para inicializar las unidades por caja
    async initializeBoxUnits() {
        if (!this.props.productId) {
            return;
        }

        try {
            // Explorar el DynamicRecordList del parent
            const parentProps = this.__owl__.parent?.props;
            if (parentProps?.list && parentProps.list.records) {
                const records = Array.isArray(parentProps.list.records) ?
                              parentProps.list.records :
                              Object.values(parentProps.list.records);

                for (const record of records) {
                    if (record.data && record.data.id === this.props.productId) {
                        // Si box_units está en el catálogo, usarlo directamente
                        if (record.data.box_units) {
                            this.boxState.unitsPerBox = record.data.box_units;

                            // Si el producto ya está en el pedido, calcular las cajas
                            if (this.isInOrder()) {
                                this.calculateBoxesFromQuantity();
                            }

                            return;
                        }
                        break;
                    }
                }
            }

            // Obtener box_units usando ORM service (estándar en Odoo 18)
            if (this.env.services?.orm) {
                try {
                    const result = await this.env.services.orm.read(
                        'product.product',
                        [this.props.productId],
                        ['box_units']
                    );

                    if (result && result[0]) {
                        const boxUnits = result[0].box_units;
                        if (boxUnits && boxUnits > 0) {
                            this.boxState.unitsPerBox = boxUnits;

                            // Si el producto ya está en el pedido, calcular las cajas
                            if (this.isInOrder()) {
                                this.calculateBoxesFromQuantity();
                            }

                            return;
                        } else {
                            // Campo existe pero es 0, false, null - usar valor por defecto
                            this.boxState.unitsPerBox = 1;

                            // Si el producto ya está en el pedido, calcular las cajas
                            if (this.isInOrder()) {
                                this.calculateBoxesFromQuantity();
                            }

                            return;
                        }
                    }
                } catch (ormError) {
                    // En caso de error, continuar con fallback
                }
            } else {
                // Fallback: usar RPC solo si ORM no está disponible
                try {
                    const result = await this.env.services.rpc({
                        model: 'product.product',
                        method: 'read',
                        args: [[this.props.productId], ['box_units']],
                    });

                    if (result && result[0]) {
                        const boxUnits = result[0].box_units;
                        if (boxUnits && boxUnits > 0) {
                            this.boxState.unitsPerBox = boxUnits;

                            // Si el producto ya está en el pedido, calcular las cajas
                            if (this.isInOrder()) {
                                this.calculateBoxesFromQuantity();
                            }

                            return;
                        } else {
                            this.boxState.unitsPerBox = 1;

                            // Si el producto ya está en el pedido, calcular las cajas
                            if (this.isInOrder()) {
                                this.calculateBoxesFromQuantity();
                            }

                            return;
                        }
                    }
                } catch (rpcError) {
                    // En caso de error, usar valor por defecto
                }
            }

        } catch (error) {
            // En caso de cualquier error, usar valor por defecto
        }

        // Si el producto ya está en el pedido, calcular las cajas incluso con los valores por defecto
        if (this.isInOrder()) {
            this.calculateBoxesFromQuantity();
        }
    },

    // Método para calcular el número de cajas a partir de la cantidad total
    calculateBoxesFromQuantity() {
        if (this.quantity && this.boxState.unitsPerBox && this.boxState.unitsPerBox > 0) {
            this.boxState.boxes = Math.floor(this.quantity / this.boxState.unitsPerBox);
        }
    },

    // Detectar cambios de productId
    onWillUpdateProps(nextProps) {
        if (this.props.productId !== nextProps.productId) {
            // Actualizar props temporalmente para la búsqueda
            const oldProps = this.props;
            this.props = nextProps;
            this.initializeBoxUnits();
            this.props = oldProps;
        }
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

    decreaseUnitsPerBox() {
        if (this.boxState.unitsPerBox > 1) {
            this.boxState.unitsPerBox--;
            this.updateQuantityFromBoxes();
        }
    },

    increaseUnitsPerBox() {
        this.boxState.unitsPerBox++;
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
