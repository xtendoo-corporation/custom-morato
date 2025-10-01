/** @odoo-module **/

import { registry } from '@web/core/registry';
import { patch } from '@web/core/utils/patch';
import { SaleOrderLineOne2Many } from '@sale/js/sale_order_line_field/sale_order_line_field';
import { SaleOrderLineListRenderer } from '@sale/js/sale_order_line_field/sale_order_line_field';

console.log('[BARCODE FIELD] Iniciando patch para campo barcode');

// Patch para el componente One2Many
patch(SaleOrderLineOne2Many.prototype, {
    setup() {
        super.setup();
        console.log('[BARCODE FIELD] Setup completado');
    },

    async _onAdd(ev) {
        // Llamar al método original
        const result = await super._onAdd(ev);

        // Después de agregar una línea, hacer focus en el campo barcode
        setTimeout(() => {
            const newBarcodeField = document.querySelector('.o_field_sol_o2m .o_data_row:last-child .o_barcode_field');
            if (newBarcodeField) {
                newBarcodeField.focus();
                console.log('[BARCODE FIELD] Focus establecido en nuevo campo barcode');
            }
        }, 100);

        return result;
    }
});

// Patch para el renderer de lista
patch(SaleOrderLineListRenderer.prototype, {
    setup() {
        super.setup();
        this._setupBarcodeFieldEvents();
    },

    _setupBarcodeFieldEvents() {
        console.log('[BARCODE FIELD] Configurando eventos para campos barcode');
    },

    async _renderView() {
        const result = await super._renderView();

        // Configurar eventos después del render
        this._setupBarcodeAutoFocus();

        return result;
    },

    _setupBarcodeAutoFocus() {
        // Auto-focus en el primer campo barcode vacío cuando se carga la vista
        setTimeout(() => {
            const firstEmptyBarcode = document.querySelector('.o_field_sol_o2m .o_barcode_field:not([value])');
            if (firstEmptyBarcode) {
                firstEmptyBarcode.focus();
                console.log('[BARCODE FIELD] Auto-focus en primer campo barcode vacío');
            }
        }, 200);

        // Configurar eventos para todos los campos barcode
        const barcodeFields = document.querySelectorAll('.o_barcode_field, .o_barcode_field_mobile');
        barcodeFields.forEach(field => {
            // Evento cuando se completa el escaneo (Enter)
            field.addEventListener('keypress', (event) => {
                if (event.key === 'Enter') {
                    console.log('[BARCODE FIELD] Enter detectado en campo barcode');
                    // El onchange se ejecutará automáticamente
                    // Hacer focus en el siguiente campo barcode después de un delay
                    setTimeout(() => {
                        this._focusNextBarcodeField();
                    }, 500);
                }
            });

            // Evento para resaltar el campo cuando tiene foco
            field.addEventListener('focus', () => {
                field.style.backgroundColor = '#e3f2fd';
                field.style.borderColor = '#007bff';
            });

            field.addEventListener('blur', () => {
                field.style.backgroundColor = '#f8fff8';
                field.style.borderColor = '#28a745';
            });
        });
    },

    _focusNextBarcodeField() {
        // Buscar el siguiente campo barcode vacío y hacer focus
        const nextEmptyBarcode = document.querySelector('.o_field_sol_o2m .o_barcode_field:not([value]):not(:focus)');
        if (nextEmptyBarcode) {
            nextEmptyBarcode.focus();
            console.log('[BARCODE FIELD] Focus movido al siguiente campo barcode');
        } else {
            // Si no hay más campos barcode, agregar una nueva línea
            console.log('[BARCODE FIELD] No hay más campos - agregando nueva línea');
            const addButton = document.querySelector('.o_field_sol_o2m .o_list_button_add');
            if (addButton) {
                addButton.click();
            }
        }
    }
});

console.log('[BARCODE FIELD] Patch aplicado correctamente');
