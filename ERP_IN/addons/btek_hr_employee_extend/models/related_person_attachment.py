# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class Atachment3d(models.Model):
    _name = 'btek.related.person.attachment'
    _inherits = {'ir.attachment': 'attachment_id'}

    related_person_id = fields.Many2one('btek.related.person', required=True)
    attachment_id = fields.Many2one('ir.attachment', required=True, ondelete="cascade")
