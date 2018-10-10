# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError
import datetime


class WizardSetupConsignment(models.TransientModel):
    _name = 'wizard.setup.consignment'

    def setup(self):
        consignment_location = self.setup_stock_location()

        return True

    @api.model
    def setup_stock_location(self):
        consignment_locations = \
            self.env['stock.location'].search(
                [('consignment', '=', True),('usage', '=', 'internal')])
        if consignment_locations:
            return consignment_locations[0]
        vals = {
            'name': _('Consignment warehouse'),
            'consignment': True
        }
        consignment_location = self.env['stock.location'].create(vals)
        return consignment_location

