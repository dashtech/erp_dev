# -*- coding: utf-8 -*-
from odoo import api, tools, fields, models, _


class CustomPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create(self, vals):
        if not vals.has_key('company_id'):
            vals['company_id'] = self.env.user.company_id.id
        vals['code'] = self.env['ir.sequence'].with_context(
                force_company=vals['company_id']).next_by_code('seq.partner') or _('New')
        return super(CustomPartner, self).create(vals)

    # @api.multi
    # def write(self, values):
    #     code = self.code or ''
    #     if not code.startswith('KH'):
    #         values['code'] = self.env['ir.sequence'].with_context(
    #             force_company=self.company_id).next_by_code('seq.partner') or code
    #     return super(CustomPartner, self).write(values)