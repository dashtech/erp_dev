# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _


class StockLocation(models.Model):
    _inherit = 'stock.location'

    consignment = fields.Boolean(default=False)




