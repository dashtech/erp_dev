# -*- coding: utf-8 -*-
from odoo import api, fields, models


class BtekPurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    partner_code = fields.Char(related='partner_id.code', string='Partner Code', readonly=True)
    address = fields.Char(related='partner_id.address', string='Address', readonly=True)