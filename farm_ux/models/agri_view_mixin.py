# -*- coding: utf-8 -*-
# [US-039-25] [LOSSLESS] [ISA-88] Advanced UI De-industrialization Engine
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from lxml import etree

class AgriViewMixin(models.AbstractModel):
    """
    Advanced de-industrialization interceptor: full-dimension view reshaping.
    Supports real-time mapping of labels, placeholders, help texts, titles
    and button strings.
    """
    _inherit = 'agri.view.mixin'
    _description = 'Global UI De-industrialization Injector'

    @api.model
    def _get_view(self, view_id=None, view_type='form', **options):
        """Core interception point: dynamically rebuild the XML arch."""
        arch, view = super()._get_view(view_id=view_id, view_type=view_type, **options)
        
        # 1. Get the term-mapping hub
        TermMapping = self.env['term.mapping']
        industry = self.env.context.get('industry_context', 'general')
        
        # 2. Breadth-first search, replacing all visible text
        # Intercept labels, strings, placeholders, help texts, titles
        for node in arch.xpath("//*[@string] | //*[@placeholder] | //*[@help]"):
            for attr in ['string', 'placeholder', 'help']:
                if node.get(attr):
                    node.set(attr, TermMapping.apply_term_mapping_to_text(node.get(attr), industry_context=industry))
        
        # 3. Intercept container-level titles (form, tree, list, kanban, search, graph, pivot)
        for node in arch.xpath("//form | //list | //tree | //kanban | //search | //graph | //pivot"):
            if node.get('string'):
                node.set('string', TermMapping.apply_term_mapping_to_text(node.get('string'), industry_context=industry))

        # 4. [Special Injection] Community-contribution warning bar
        if view_type == 'form' and self._name in ['mrp.production', 'stock.lot', 'res.partner']:
            if 'agri.clearing.ledger' in self.env:
                try:
                    todo_count = self.env['agri.clearing.ledger'].sudo().search_count([('state', '=', 'draft')])
                    if todo_count > 0:
                        alert_div = etree.Element('div', {
                            'class': 'alert alert-info text-center',
                            'role': 'alert',
                            'style': 'margin-bottom: 8px; font-weight: bold; border-left: 5px solid #28a745;'
                        })
                        alert_div.text = _("🌱 %d Agricultural Contributions awaiting verification.") % todo_count
                        header = arch.xpath("//header")
                        if header: header[0].addprevious(alert_div)
                        else: arch.insert(0, alert_div)
                except:
                    pass

        return arch, view

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        """Intercept field definitions, replacing selection labels and field strings in real time."""
        res = super(AgriViewMixin, self).fields_get(allfields=allfields, attributes=attributes)
        if self.env.context.get('skip_agri_mapping'):
            return res

        TermMapping = self.env['term.mapping']
        industry = self.env.context.get('industry_context', 'general')

        for field_name, field_def in res.items():
            # 1. Replace the field's main label
            if 'string' in field_def:
                field_def['string'] = TermMapping.apply_term_mapping_to_text(field_def['string'], industry_context=industry)
            
            # 2. Replace selection option labels
            if 'selection' in field_def and isinstance(field_def['selection'], list):
                new_selection = []
                for key, label in field_def['selection']:
                    new_selection.append((key, TermMapping.apply_term_mapping_to_text(label, industry_context=industry)))
                field_def['selection'] = new_selection

        return res

    @api.depends_context('industry_context', 'lang')
    def _compute_display_name(self):
        """Intercept display-name computation, replacing industrial terms in real time."""
        super()._compute_display_name()
        if self.env.context.get('skip_agri_mapping'):
            return

        TermMapping = self.env['term.mapping']
        industry = self.env.context.get('industry_context', 'general')

        for rec in self:
            if rec.display_name:
                rec.display_name = TermMapping.apply_term_mapping_to_text(rec.display_name, industry_context=industry)

    def translate_exception(self, exception_msg):
        """Translate low-level manufacturing errors into agricultural wording."""
        mapping = {
            'manufacturing order': _('agricultural intervention'),
            'bill of materials': _('cultivation recipe'),
            'work order': _('field task'),
            'insufficient stock': _('insufficient input evidence'),
            'inventory': _('resource registry'),
        }
        translated_msg = exception_msg.lower()
        for industrial, agri in mapping.items():
            translated_msg = translated_msg.replace(industrial, agri)
        return translated_msg.capitalize()

    def handle_validation_error(self, e):
        """Hook model validation errors."""
        agri_msg = self.translate_exception(str(e))
        raise ValidationError(agri_msg)
