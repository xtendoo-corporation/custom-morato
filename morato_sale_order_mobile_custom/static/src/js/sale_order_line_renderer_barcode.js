/** @odoo-module **/

import { registry } from '@web/core/registry';
import { patch } from '@web/core/utils/patch';
import { ListRenderer } from "@web/views/list/list_renderer";
import { X2ManyField } from "@web/views/fields/x2many/x2many_field";

console.log('[BARCODE FIELD] Iniciando patch para campo barcode');

// Patch para X2ManyField (campo One2Many/Many2Many)
patch(X2ManyField.prototype, {
    setup() {
        super.setup();
        console.log('[BARCODE FIELD] X2ManyField Setup completado');

        // Observar cambios después del guardado
        this._observeChanges();
    },

    _observeChanges() {
        // Observer para detectar cuando se agregan nuevas líneas
        setTimeout(() => {
            const observer = new MutationObserver((mutations) => {
                for (const mutation of mutations) {
                    if (mutation.addedNodes.length > 0) {
                        setTimeout(() => {
                            this._autoFocusBarcode();
                        }, 150);
                        break;
                    }
                }
            });

            const container = document.querySelector('.o_field_one2many, .o_field_many2many');
            if (container) {
                observer.observe(container, {
                    childList: true,
                    subtree: true
                });
                console.log('[BARCODE FIELD] Observer configurado');
            }
        }, 300);
    },

    _autoFocusBarcode() {
        const lastBarcodeField = document.querySelector('.o_data_row:last-child .o_barcode_field_mobile input, .o_data_row:last-child .o_barcode_field input');

        if (lastBarcodeField && document.activeElement !== lastBarcodeField) {
            lastBarcodeField.focus();

            if (typeof lastBarcodeField.select === 'function') {
                lastBarcodeField.select();
            }

            console.log('[BARCODE FIELD] Focus establecido en último barcode');
        }
    }
});

// Patch para ListRenderer (manejo de eventos de teclado)
patch(ListRenderer.prototype, {
    setup() {
        super.setup();
        console.log('[BARCODE FIELD] ListRenderer Setup completado');
    },

    async onCellKeydown(hotkey, ev) {
        const result = await super.onCellKeydown(hotkey, ev);

        // Detectar Enter en campo barcode
        if (hotkey === 'enter' &&
            (ev.target.classList.contains('o_barcode_field_mobile') ||
             ev.target.classList.contains('o_barcode_field'))) {

            console.log('[BARCODE FIELD] Enter detectado en barcode');
            ev.preventDefault();
            ev.stopPropagation();

            // Agregar nueva línea
            setTimeout(() => {
                const addButton = document.querySelector('.o_field_x2many_list_row_add a');
                if (addButton) {
                    console.log('[BARCODE FIELD] Agregando nueva línea');
                    addButton.click();

                    // Enfocar el nuevo campo barcode
                    setTimeout(() => {
                        const newBarcode = document.querySelector('.o_data_row:last-child .o_barcode_field_mobile input, .o_data_row:last-child .o_barcode_field input');
                        if (newBarcode) {
                            newBarcode.focus();

                            if (typeof newBarcode.select === 'function') {
                                newBarcode.select();
                            }

                            console.log('[BARCODE FIELD] Nuevo barcode enfocado');
                        }
                    }, 200);
                }
            }, 100);
        }

        return result;
    }
});

// Sistema de respaldo con intervalo
let autofocusInterval;
let lastFocusedElement = null;

function startBarcodeAutofocus() {
    console.log('[BARCODE FIELD] Sistema de respaldo iniciado');

    autofocusInterval = setInterval(() => {
        // No hacer nada si ya hay un barcode enfocado
        const activeEl = document.activeElement;
        if (activeEl?.classList.contains('o_barcode_field_mobile') ||
            activeEl?.classList.contains('o_barcode_field')) {
            lastFocusedElement = activeEl;
            return;
        }

        // Buscar el último campo barcode vacío
        const allBarcodes = Array.from(
            document.querySelectorAll('.o_barcode_field_mobile input, .o_barcode_field input')
        );

        const lastEmptyBarcode = allBarcodes.reverse().find(field => !field.value);

        if (lastEmptyBarcode && lastEmptyBarcode !== lastFocusedElement) {
            lastEmptyBarcode.focus();

            if (typeof lastEmptyBarcode.select === 'function') {
                lastEmptyBarcode.select();
            }

            lastFocusedElement = lastEmptyBarcode;
            console.log('[BARCODE FIELD] Autofocus de respaldo aplicado');
        }
    }, 500);
}

// Iniciar sistema de respaldo
setTimeout(startBarcodeAutofocus, 1500);
