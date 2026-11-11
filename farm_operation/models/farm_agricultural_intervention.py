# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
import logging

_logger = logging.getLogger(__name__)


class AgriInterventionIsl(models.Model):
    """
    Concrete ISL model for Agricultural Interventions using _inherits.
    This model inherits from the base mrp.production model and includes the shared logic from the mixin.
    Refactored from farm.agricultural.intervention with 100% logic and comment retention.
    """
    _name = 'agri.intervention'
    _description = 'Agricultural Intervention (ISL Layer)'
    _inherits = {'mrp.production': 'production_id'}  # Inherit from base Odoo model
    _inherit = ['mail.thread', 'mail.activity.mixin', 'agri.intervention.mixin']  # Include shared logic

    # Link to the base model (this field is required for _inherits)
    production_id = fields.Many2one(
        'mrp.production',
        string="Base Production Order",
        required=True,
        ondelete="cascade"
    )

    # Add any agricultural-specific fields that extend beyond the base model
    # The mixin already provides most agricultural-specific functionality

    @api.model_create_multi
    def create(self, vals_list):
        """Propagate ``intervention_type`` to the auto-created MO (B4 fix).

        ``agri.intervention`` and ``mrp.production`` both define a stored
        field named ``intervention_type`` with the same 10-value selection
        (aligned by the B7 fix: the mixin selection now also contains
        ``'process'``, like the MO's, whose default is ``'process'``).
        Because the child redefines the field, Odoo's ``_inherits``
        create puts the value in the child's own table only
        (``field.inherited`` is False for a redefined field, see
        ``odoo/models.py`` ``create()``) and the parent MO is created
        with its default ``'process'``. The MO form's "Soil Nutrient
        Balance" page (``invisible="intervention_type not in
        ['fertilizing', 'tillage']"``) and the ``agri_spatial_gauge``
        widget therefore never trigger on the real flow, even though
        the intervention itself is e.g. ``'fertilizing'``.

        A ``related``/computed field on the MO is not possible here:
        the MO has no link back to its intervention (the link points
        the other way, ``production_id``), and a compute that searches
        ``agri.intervention`` on every MO would also overwrite the
        type of standalone MOs created directly via
        ``mrp.production`` (which legitimately carry their own
        ``intervention_type``). Propagating once, at create, from the
        intervention to the MO it just created is the minimal fix.

        Only MO records auto-created by this ``create()`` are touched:
        when ``production_id`` is given explicitly in ``vals`` the
        caller linked a pre-existing MO and its type is left alone.
        A later change of the intervention's type is deliberately NOT
        synced (create-only, per the batch-2 simulation decision);
        if live sync is ever wanted, add the same propagation to
        ``write()``.

        B7c fallback: the intervention's ``name`` is the child's OWN
        field (defined by ``agri.intervention.base``, not delegated
        from ``mrp.production`` — ``_add_inherited_fields`` only adds
        parent fields "not redefined locally"), so a name typed in
        the dedicated form view is stored on the intervention and the
        auto-created MO still gets its own sequence number (the
        parent's ``create()`` only sequences a name that is missing
        or ``'New'``). No ``create()`` hack is needed to preserve a
        typed name. The only gap is a name left untouched at
        ``'New'``: it would otherwise be stored literally as
        ``'New'`` on the intervention, so it is replaced here with
        the auto-created MO's sequence name (``WH/MO/xxxxx``).
        """
        records = super().create(vals_list)
        mo_selection = dict(
            self.env['mrp.production']._fields['intervention_type'].selection
        )
        for vals, rec in zip(vals_list, records):
            if 'production_id' in vals:
                continue
            itype = rec.intervention_type
            if not itype:
                continue
            if itype not in mo_selection:
                # Defensive: the mixin selection may one day gain a value
                # the MO selection lacks; never let that break creation.
                _logger.warning(
                    "Agri Intervention %s: intervention_type %r is not a "
                    "valid mrp.production intervention_type, not "
                    "propagated to MO %s.",
                    rec.id, itype,
                    rec.production_id.id if rec.production_id else False,
                )
                continue
            if rec.production_id and rec.production_id.intervention_type != itype:
                rec.production_id.write({'intervention_type': itype})
        for rec in records:
            if rec.production_id and (not rec.name or rec.name == _('New')):
                rec.name = rec.production_id.name
        return records
