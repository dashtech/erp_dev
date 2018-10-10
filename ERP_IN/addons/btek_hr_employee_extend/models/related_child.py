# -*- coding: utf-8 -*-
from odoo import fields, models


class RelatedChild(models.Model):
    _name = 'btek.related.child'

    employee_id = fields.Many2one('hr.employee')
    name = fields.Char(u'Họ tên')
    birthday = fields.Date(u'Ngày sinh')
    gender = fields.Selection([('male', u'Nam'), ('female', u'Nữ')],
                              string=u'Giới tính')
    note = fields.Char(u'Ghi chú')
