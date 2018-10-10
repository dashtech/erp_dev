# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class MailMessage(models.Model):
    _inherit = 'mail.message'

    sent = fields.Boolean(string='Sent to mobile',
                          default=False)
    readed = fields.Boolean(string='Read',
                          default=False)

    @api.cr_uid_context
    def get_message(self, cr, uid, context=None):
        return self.browse(1).get_unsent_message()

    def get_tracking(self, message):
        res = {}
        for value in message.tracking_value_ids:
            old_value = value.get_old_display_value()[0]
            new_value = value.get_new_display_value()[0]

            if old_value == new_value:
                continue
            res[value.field_desc] = {
                'old_value': unicode(old_value),
                'new_value': unicode(new_value),
            }
        return res

    def setread(self):
        return self.write({'readed': True})

    def setsent(self):
        return self.write({'sent': True})
