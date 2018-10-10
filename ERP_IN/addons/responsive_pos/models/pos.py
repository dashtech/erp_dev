# -*- coding: utf-8 -*-

from odoo import fields, models,tools,api
import logging

class pos_config(models.Model):
    _inherit = 'pos.config' 

    allow_responsive_screen = fields.Boolean('Allow Responsive Screen',default=True)
    allow_bottom_buttons = fields.Boolean('Allow bottom buttons',default=True)




