/** @odoo-module **/

import { registry } from '@web/core/registry';
import { patch } from '@web/core/utils/patch';
import { useService } from "@web/core/utils/hooks";
import { SaleOrderLineOne2Many } from '@sale/js/sale_order_line_field/sale_order_line_field';

console.log('[BARCODE PATCH] Iniciando patch de SaleOrderLineOne2Many para vista móvil');

// Patch para el componente principal One2Many
patch(SaleOrderLineOne2Many.prototype, {
    setup() {
        console.log('[BARCODE PATCH] Setup One2Many ejecutado');
        super.setup();
        this.orm = useService("orm");
        this.notification = useService("notification");
        this._setupBarcodeListener();
        this.isActive = false;
        console.log('[BARCODE PATCH] One2Many setup completado - listener configurado');
    },

    _setupBarcodeListener() {
        console.log('[BARCODE PATCH] Configurando listener global de código de barras');
        this.barcodeBuffer = '';
        this.barcodeTimeout = null;
        this._boundKeyPressHandler = this._onKeyPress.bind(this);
        this._boundFocusHandler = this._onFocusIn.bind(this);
        this._boundBlurHandler = this._onFocusOut.bind(this);

        // Agregar listeners globales
        document.addEventListener('keypress', this._boundKeyPressHandler);
        document.addEventListener('focusin', this._boundFocusHandler);
        document.addEventListener('focusout', this._boundBlurHandler);

        console.log('[BARCODE PATCH] Event listeners globales agregados');
    },

    willUnmount() {
        console.log('[BARCODE PATCH] One2Many desmontándose - limpiando listeners');
        super.willUnmount?.();

        if (this._boundKeyPressHandler) {
            document.removeEventListener('keypress', this._boundKeyPressHandler);
        }
        if (this._boundFocusHandler) {
            document.removeEventListener('focusin', this._boundFocusHandler);
        }
        if (this._boundBlurHandler) {
            document.removeEventListener('focusout', this._boundBlurHandler);
        }
        if (this.barcodeTimeout) {
            clearTimeout(this.barcodeTimeout);
        }
        console.log('[BARCODE PATCH] Event listeners removidos');
    },

    _onFocusIn(event) {
        // Activar si el foco está en el área de líneas de pedido
        const isInOrderLines = event.target.closest('.o_field_sol_o2m') ||
                              event.target.closest('.o_form_view') &&
                              document.querySelector('.o_field_sol_o2m');

        if (isInOrderLines) {
            console.log('[BARCODE PATCH] Área de líneas de pedido activa - listo para escanear');
            this.isActive = true;
        }
    },

    _onFocusOut(event) {
        // Mantener activo si seguimos en el área de líneas
        setTimeout(() => {
            const isStillInOrderLines = document.activeElement?.closest('.o_field_sol_o2m') ||
                                       document.activeElement?.closest('.o_form_view');
            if (!isStillInOrderLines) {
                console.log('[BARCODE PATCH] Saliendo del área de líneas - desactivando');
                this.isActive = false;
            }
        }, 100);
    },

    _onKeyPress(event) {
        // Solo procesar si estamos activos Y en una vista de pedido de venta
        if (!this.isActive) {
            return;
        }

        const isInSaleOrder = event.target.closest('.o_form_view') &&
                             document.querySelector('.o_field_sol_o2m');
        if (!isInSaleOrder) {
            return;
        }

        // NO ignorar si estamos en inputs - permitir escaneo en cualquier momento
        // Solo ignorar si estamos editando activamente un campo de texto largo
        if (event.target.tagName === 'TEXTAREA' && event.target.value.length > 0) {
            return;
        }

        console.log(`[BARCODE PATCH] Tecla presionada: ${event.key}, Buffer: "${this.barcodeBuffer}"`);

        // Si presiona Enter, procesar el código de barras
        if (event.key === 'Enter' && this.barcodeBuffer) {
            console.log(`[BARCODE PATCH] Enter detectado - procesando: "${this.barcodeBuffer}"`);
            event.preventDefault();
            event.stopPropagation();
            this._processBarcode(this.barcodeBuffer.trim());
            this.barcodeBuffer = '';
            return;
        }

        // Acumular caracteres del código de barras (incluyendo más caracteres especiales)
        if (event.key.match(/[a-zA-Z0-9\-_.@#]/)) {
            this.barcodeBuffer += event.key;
            console.log(`[BARCODE PATCH] Buffer actualizado: "${this.barcodeBuffer}"`);

            // Reiniciar timeout
            if (this.barcodeTimeout) {
                clearTimeout(this.barcodeTimeout);
            }

            // Timeout más corto para respuesta más rápida
            this.barcodeTimeout = setTimeout(() => {
                if (this.barcodeBuffer && this.barcodeBuffer.length >= 4) {
                    console.log(`[BARCODE PATCH] Timeout - procesando: "${this.barcodeBuffer}"`);
                    this._processBarcode(this.barcodeBuffer.trim());
                    this.barcodeBuffer = '';
                }
            }, 200);
        }

        // Limpiar buffer si se presiona una tecla no válida
        if (event.key === ' ' || event.key === 'Escape') {
            console.log('[BARCODE PATCH] Buffer limpiado por tecla especial');
            this.barcodeBuffer = '';
            if (this.barcodeTimeout) {
                clearTimeout(this.barcodeTimeout);
            }
        }
    },

    async _processBarcode(barcode) {
        console.log(`[BARCODE PATCH] Procesando código de barras: "${barcode}"`);

        if (!barcode || barcode.length < 4) {
            console.log('[BARCODE PATCH] Código muy corto - ignorando');
            return;
        }

        try {
            console.log('[BARCODE PATCH] Buscando producto...');

            const products = await this.orm.searchRead(
                "product.product",
                [
                    ["barcode", "=", barcode],
                    ["sale_ok", "=", true]
                ],
                ["id", "display_name", "list_price", "uom_id", "taxes_id"]
            );

            console.log(`[BARCODE PATCH] Productos encontrados: ${products.length}`, products);

            if (products.length > 0) {
                const product = products[0];
                console.log(`[BARCODE PATCH] Agregando producto: ${product.display_name}`);

                const success = await this._addProductFromBarcode(product);

                if (success) {
                    // Mostrar notificación de éxito
                    this.notification.add(
                        `✅ Producto agregado: ${product.display_name}`,
                        {
                            type: "success",
                            sticky: false
                        }
                    );
                    console.log('[BARCODE PATCH] Notificación de éxito mostrada');
                }
            } else {
                console.log(`[BARCODE PATCH] Producto no encontrado: "${barcode}"`);
                this.notification.add(
                    `❌ Código "${barcode}" no encontrado`,
                    {
                        type: "warning",
                        sticky: false
                    }
                );
            }
        } catch (error) {
            console.error("[BARCODE PATCH] Error procesando código:", error);
            this.notification.add(
                "❌ Error al procesar código de barras",
                {
                    type: "danger",
                    sticky: false
                }
            );
        }
    },

    async _addProductFromBarcode(product) {
        console.log(`[BARCODE PATCH] Agregando producto automáticamente:`, product);

        try {
            if (!this.props.record) {
                console.error('[BARCODE PATCH] No hay registro disponible');
                return false;
            }

            const orderLines = this.props.record.data.order_line;
            console.log('[BARCODE PATCH] Accediendo a order_line:', orderLines);

            // Verificar si el producto ya existe y aumentar cantidad
            const existingLine = orderLines.records.find(record =>
                record.data.product_id && record.data.product_id[0] === product.id
            );

            if (existingLine) {
                console.log('[BARCODE PATCH] Producto ya existe - aumentando cantidad');
                const newQty = existingLine.data.product_uom_qty + 1;
                await existingLine.update({ product_uom_qty: newQty });

                this.notification.add(
                    `✅ Cantidad actualizada: ${product.display_name} (${newQty})`,
                    {
                        type: "info",
                        sticky: false
                    }
                );
                return true;
            } else {
                console.log('[BARCODE PATCH] Creando nueva línea directamente en sale.order.line');

                // Crear la línea directamente en el modelo sale.order.line
                const lineData = {
                    order_id: this.props.record.resId,
                    product_id: product.id,
                    product_uom_qty: 1,
                    sequence: (orderLines.records.length + 1) * 10,
                };

                console.log('[BARCODE PATCH] Datos de línea a crear:', lineData);

                // Crear línea directamente - esto ya funciona
                const newLineId = await this.orm.call(
                    'sale.order.line',
                    'create',
                    [lineData]
                );

                console.log('[BARCODE PATCH] Nueva línea creada con ID:', newLineId);

                // En lugar de product_id_change, ejecutar onchange directamente en la línea
                try {
                    await this.orm.call(
                        'sale.order.line',
                        '_onchange_product_id',
                        [newLineId]
                    );
                    console.log('[BARCODE PATCH] Onchange ejecutado correctamente');
                } catch (onchangeError) {
                    console.log('[BARCODE PATCH] Onchange falló, usando write para actualizar campos');

                    // Si el onchange falla, actualizar manualmente los campos principales
                    await this.orm.call(
                        'sale.order.line',
                        'write',
                        [
                            newLineId,
                            {
                                'name': product.display_name,
                                'price_unit': product.list_price || 0,
                                'product_uom': product.uom_id ? product.uom_id[0] : false,
                            }
                        ]
                    );
                    console.log('[BARCODE PATCH] Campos actualizados manualmente');
                }

                // Recargar el registro padre para refrescar la vista
                await this.props.record.load();
                console.log('[BARCODE PATCH] Registro padre recargado');

                return true;
            }

        } catch (error) {
            console.error("[BARCODE PATCH] Error agregando producto:", error);

            // Método de respaldo: usar comandos de Odoo para agregar la línea
            try {
                console.log('[BARCODE PATCH] Intentando método de respaldo con comandos...');

                const currentOrderLines = this.props.record.data.order_line;

                // Crear comando de Odoo para agregar nueva línea
                const newLineCommand = [0, 0, {
                    product_id: product.id,
                    product_uom_qty: 1,
                    name: product.display_name,
                    price_unit: product.list_price || 0,
                    sequence: (currentOrderLines.records.length + 1) * 10,
                }];

                // Actualizar el record usando comandos de Odoo
                await this.props.record.update({
                    order_line: [newLineCommand]
                });

                console.log('[BARCODE PATCH] Producto agregado con método de respaldo');

                this.notification.add(
                    `✅ Producto agregado: ${product.display_name}`,
                    {
                        type: "success",
                        sticky: false
                    }
                );

                return true;

            } catch (backupError) {
                console.error("[BARCODE PATCH] Error con método de respaldo:", backupError);

                this.notification.add(
                    `❌ Error al agregar "${product.display_name}"`,
                    {
                        type: "danger",
                        sticky: false
                    }
                );
                return false;
            }
        }
    }
});

console.log('[BARCODE PATCH] Patch aplicado correctamente para vista móvil');
