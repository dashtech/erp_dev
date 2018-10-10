# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import ValidationError, UserError


class PackOperation(models.Model):
    _inherit = "stock.pack.operation"

    @api.multi
    def write(self, values):
        res = super(PackOperation, self).write(values)
        if values.has_key('qty_done'):
            if values['qty_done'] > self.product_qty:
                raise UserError(_('You can not set quantity done greater quantity need move!'))
        return res
