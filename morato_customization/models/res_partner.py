from odoo import models, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.depends('is_company', 'name', 'parent_id.name', 'type', 'company_name', 'commercial_company_name')
    def _compute_complete_name(self):
        for partner in self:
            # Llamar a _get_complete_name sin incluir el nombre comercial
            partner.complete_name = partner.with_context(force_no_commercial=True)._get_complete_name()

    def _get_complete_name(self):
        # Copia del método original, pero sin añadir el nombre comercial
        self.ensure_one()
        names = []
        if self.parent_id and self.parent_id != self:
            names.append(self.parent_id.name)
        if self.type and self.type != 'contact':
            names.append(dict(self._fields['type'].selection).get(self.type))
        if self.company_name:
            names.append(self.company_name)
        names.append(self.name or '')
        return ", ".join(filter(None, names))

    def name_get(self):
        return super().name_get()
