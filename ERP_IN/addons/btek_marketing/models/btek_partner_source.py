#!/usr/bin/python
# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _


class btek_partner_source(models.Model):
    _name = 'btek.partner.source'

    name = fields.Char(string="Name", copy=False, default=lambda self: _('New'))
    description = fields.Text(string='Description')
    code = fields.Char(string="Code")


    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    'btek.partner.source') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('btek.partner.source') or _('New')

        result = super(btek_partner_source, self).create(vals)
        return result

class btek_partner_group(models.Model):
    _inherit = 'btek.partner.group'

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    'btek.partner.group') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('btek.partner.group') or _('New')

        result = super(btek_partner_group, self).create(vals)
        return result
