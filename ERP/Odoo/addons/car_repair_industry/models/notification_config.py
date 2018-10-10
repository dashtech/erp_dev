# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class NotificationLine(models.Model):
    _name = 'fleet.notification.line'

    sequence = fields.Char('Sequence')
    model_id = fields.Many2one('ir.model', 'Table')
    type = fields.Selection([('create', 'Create'), ('Edit', 'Edit'), ('delete', 'Delete'),
                             ('confirm', 'Confirm'),
                             ('cancel', 'Cancel'),
                             ('mark_win', 'Mark Win'),
                             ('mark_lost', 'Mark Lost'),
                             ('stock_in', 'Stock In'),
                             ('stock_out', 'Stock Out'),
                             ('start', 'Start'),
                             ('inv_warning', 'Inventory Warning'),
                             ], string="Action Type")
    noti_id = fields.Many2one('fleet.notification', 'Notification')

    # @api.model
    # def create(self, vals):
    #     vals['sequence'] = self.env['ir.sequence'].next_by_code('fleet.notification.line')
    #     res = super(NotificationLine, self).create(vals)
    #     return res


class NotificationConfig(models.Model):
    _name = 'fleet.notification'

    name = fields.Char('Name')
    active = fields.Boolean('Active')
    noti_line_ids = fields.One2many('fleet.notification.line', 'noti_id')
