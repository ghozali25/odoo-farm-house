# -*- coding: utf-8 -*-
# [US-039-25] [LOSSLESS] Global UI Injection Center
from odoo import models

# --- Production/operation layer injection ---
class ProductionInjection(models.Model):
    _name = 'mrp.production'
    _inherit = ['mrp.production', 'agri.view.mixin']

class BomInjection(models.Model):
    _name = 'mrp.bom'
    _inherit = ['mrp.bom', 'agri.view.mixin']

class WorkcenterInjection(models.Model):
    _name = 'mrp.workcenter'
    _inherit = ['mrp.workcenter', 'agri.view.mixin']

# --- Stock/resource layer injection ---
class PickingInjection(models.Model):
    _name = 'stock.picking'
    _inherit = ['stock.picking', 'agri.view.mixin']

class MoveInjection(models.Model):
    _name = 'stock.move'
    _inherit = ['stock.move', 'agri.view.mixin']

class QuantInjection(models.Model):
    _name = 'stock.quant'
    _inherit = ['stock.quant', 'agri.view.mixin']

# --- Base/trade layer injection ---
class ProductInjection(models.Model):
    _name = 'product.template'
    _inherit = ['product.template', 'agri.view.mixin']

class PartnerInjection(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner', 'agri.view.mixin']