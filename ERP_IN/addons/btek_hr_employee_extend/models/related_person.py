# -*- coding: utf-8 -*-
from odoo import fields, models


class RelatedPerson(models.Model):
    _name = 'btek.related.person'

    employee_id = fields.Many2one('hr.employee')
    name = fields.Char(u'Họ tên')
    birthday = fields.Date(u'Ngày sinh')
    gender = fields.Selection([('male', u'Nam'), ('female', u'Nữ')],
                              string=u'Giới tính')
    x_identity_number = fields.Char(u'Số CMND')
    identity_date = fields.Date(u'Ngày cấp')
    identity_place = fields.Char(u'Nơi cấp')
    relation = fields.Char(u'Quan hệ')
    date_begin = fields.Date(u'Giảm trừ từ ngày')
    mobile = fields.Char(u'Số điện thoại')
    attachment = fields.One2many('btek.related.person.attachment',
                                 'related_person_id', string=u'các file đính kèm')
