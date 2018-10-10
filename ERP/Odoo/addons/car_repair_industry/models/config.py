# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class Company(models.Model):
    _inherit = 'res.company'

    picking_auto_done = fields.Boolean()
    workorder_auto_done = fields.Boolean()


class RepairConfigSettings(models.TransientModel):
    _name = 'repair.config.settings'
    _inherit = 'res.config.settings'

    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        default=lambda self: self.env.user.company_id)
    picking_auto_done = fields.Boolean(
        related='company_id.picking_auto_done')
    workorder_auto_done = fields.Boolean(
        related='company_id.workorder_auto_done')
