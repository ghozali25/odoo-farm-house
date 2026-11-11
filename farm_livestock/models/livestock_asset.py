# -*- coding: utf-8 -*-
from odoo import models, fields

class FarmLivestockAsset(models.Model):
    _name = 'farm.livestock.asset'
    _description = 'Livestock Biological Asset'

    ear_tag_code = fields.Char("Ear Tag Code", required=True)
    species = fields.Char("Species")
