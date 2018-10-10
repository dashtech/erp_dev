#!/usr/bin/python
# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _


class btek_accessary_asset(models.Model):
    _name = 'btek.accessary.asset'

    x_name = fields.Char(string=_('Tên'))
    x_product_uom = fields.Many2one('product.uom', string=_('Đơn vị'))
    x_qty = fields.Float(string=_('Số lượng'))
    x_price = fields.Float(string=_('Đơn giá'))
    asset_id = fields.Many2one('account.asset.asset')

