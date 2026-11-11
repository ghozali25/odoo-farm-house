# -*- coding: utf-8 -*-
from odoo import models, fields

class FarmCropCycle(models.Model):
    _name = 'farm.crop.cycle'
    _description = 'Crop Growth Cycle'

    name = fields.Char("Cycle Name", required=True)
