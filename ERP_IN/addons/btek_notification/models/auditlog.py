# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class auditlog_log(models.Model):
    _inherit = 'auditlog.log'

    proccessed = fields.Boolean(default=False)
