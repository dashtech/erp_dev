# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class be_dynamic_mapping(models.Model):
    _name = "be.dynamic.mapping"
    _description = "be.dynamic.mapping"
    _rec_name = 'view_type'

    view_type = fields.Char()
    view_code = fields.Char()
    view_ref_id = fields.Char()
    erp_model = fields.Char()
    erp_ref_id = fields.Integer()
    value = fields.Char()
    state = fields.Boolean(default=True)
    description = fields.Char()
