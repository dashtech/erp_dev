#!/usr/bin/python
# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import datetime


class BtekAutoCondition(models.Model):
    _name = 'btek.auto.condition'

    name = fields.Selection([('birth_day', 'Birthday'),
                             ('create_date', 'Create day'),
                             ('write_date', 'Write date'),
                             ('date_insurance', 'Date insurance'),
                             ('relate_lastday', 'Last day of sale')])

    operator = fields.Selection([
        ('<', 'Less Than'),
        ('<=', 'Less Than or Equal To'),
        ('=', 'Equal'),
        ('>', 'Greater Than'),
        ('>=', 'Greater Than or Equal To'),
        ('!=', 'notEqual'),
    ], string='Compare')

    option_date_define = fields.Selection([('current_day', 'Current day'),
                                           ('current_month_day', 'Current month and day'),
                                           ('current_month', 'Current month'),
                                           ('current_year', 'Current year'),
                                           ('numbers_days_before', 'Days before'),
                                           ('numbers_days_after', 'Days after')])
    numbers_days = fields.Integer()
    value_compare = fields.Char(compute='_compute_value_compare', readonly=True, store=True)
    value_display = fields.Char(compute='_compute_value_display', readonly=True)

    btek_auto_send_id = fields.Many2one('btek_auto_send')


    @api.onchange('name')
    def _change_name(self):
        self.numbers_days = False
        self.value_compare = False
        self.value_display = False

    @api.multi
    @api.depends('name', 'option_date_define')
    def _compute_value_compare(self):
        for s in self:
            if s.option_date_define:
                s.value_compare = s.option_date_define

    def tr(self, field_name):
        uid = self.env.uid
        user = self.env['res.users'].browse(uid)
        lang = user.partner_id.lang
        model_name = 'btek.auto.condition'

        name = model_name + ',' + field_name

        trans = self.env['ir.translation'].search_read(
            [('lang', '=', lang),
             ('type', '=', 'selection'),
             ('name', '=', name)],
            ['source', 'value']
        )
        res = dict((tran['source'], tran['value']) for tran in trans)
        return res

    @api.multi
    @api.depends('name', 'option_date_define', 'value_compare', 'numbers_days')
    def _compute_value_display(self):
        uid = self.env.uid
        user = self.env['res.users'].browse(uid)
        model_bject = self.env['btek.auto.condition'].with_context(
            lang=user.partner_id.lang)
        field = model_bject._fields['option_date_define']
        # dict_option_date_define = dict(field.selection)
        selection = field.selection
        tr_dict = self.tr('option_date_define')
        dict_option_date_define = \
            dict((s[0], tr_dict.get(s[1], s[1])) for s in selection)

        for s in self:
            prefix_day = ''
            if s.option_date_define in ('numbers_days_before', 'numbers_days_after'):
                prefix_day = str(s.numbers_days) + ' '
            s.value_display = prefix_day + unicode(dict_option_date_define.get(s.value_compare))
