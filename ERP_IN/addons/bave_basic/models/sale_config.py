# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class PurchaseOrderInherit(models.TransientModel):
    _inherit = 'sale.config.settings'

    def get_config(self):
        self.env.cr.execute(
            'select auto_picking_sale from sale_config_settings order by id DESC limit 1')
        result = self.env.cr.fetchone()
        if not result or 'auto' in result:
            res = 'auto'
        else:
            res = 'non_auto'
        return res

    auto_picking_sale = fields.Selection([('auto', _('Allow auto picking out')),
                                     ('non_auto', _('Not allow auto picking out'))], default=get_config,
                                    string='Auto Picking out')
