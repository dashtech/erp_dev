# -*- coding: utf-8 -*-
from odoo import api, tools, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError


class QuotationRequest(models.Model):
    _name = "quotation.request"
    _description = "Quotation Request"

    def _default_provider(self):
        uid_ = self.env.user.id
        providers = self.env['service.provider'].search([
            ('user_id', '=', uid_)])
        if not providers:
            return
        return providers[0].id

    name = fields.Char(
        required=1, readonly=True,
        string='STT')
    service_provider_id = fields.Many2one('service.provider', 'Service provider',
                                          default=_default_provider, required=1)
    member_id = fields.Many2one(
        'member', required=1,
        string='Member')
    mobile_phone = fields.Char(
        related='member_id.mobile_phone',
        store=False, readonly=True)
    vehicle_id = fields.Many2one('vehicle',
                                 string='Plate')
    vehicle_type = fields.Char(
        'Vehicle type', related='vehicle_id.vehicle_type',
        store=False, readonly=True)
    request = fields.Char(required=1)
    image_ids = fields.Many2many(
        'ir.attachment', 'quotation_image_rel',
        'quotation_id', 'attachment_id',
        'Images')
    state = fields.Selection([('draft', 'Draft'), ('seen', 'Seen'), ('contacted', 'Contacted'),
                              ('replied', 'Replied'), ('done', 'Done'),
                              ('cancel', 'Cancel')], required=1, default='draft')
    replied_datetime = fields.Datetime()
    replied_user_id = fields.Many2one('res.users', 'Replied user')
    done_datetime = fields.Datetime()
    cancel_datetime = fields.Datetime()
    quotation_detail = fields.One2many('quotation.request.detail', 'req_quotation_id')
    sale_order_id = fields.Integer('Sale order')
    notif = fields.Char('Notify')
    type = fields.Char()
    reply_content = fields.Char('Customer note')


    _sql_constraints = [
        ('quotation_name_unique', 'UNIQUE(name)',
         _('STT must be unique!')),
    ]

    @api.model
    def create(self, vals):
        name = self.env['ir.sequence'].next_by_code('quotation.request')
        vals['name'] = name
        return super(QuotationRequest, self).create(vals)

    @api.multi
    def draft_to_replied(self):
        vals = {
            'state': 'replied',
            'replied_datetime': datetime.now(),
            'replied_user_id': self.env.user.id,
        }
        self.write(vals)
        return True

    @api.multi
    def to_contacted(self):
        vals = {
            'state': 'contacted',
        }
        self.write(vals)
        return True

    @api.multi
    def replied_to_done(self):
        vals = {
            'state': 'done',
            'done_datetime': datetime.now(),
        }
        self.write(vals)
        return True

    @api.multi
    def to_cancel(self):
        vals = {
            'state': 'cancel',
            'cancel_datetime': datetime.now(),
        }
        self.write(vals)
        return True

    # @api.multi
    # def read(self, fields=[], load='_classic_read'):
    #     uid, password, db, sock = self.connect()
    #     res = sock.execute(db, uid, password,
    #                        self._name, 'read',
    #                        self._ids, fields,
    #                        load)
    #     if 'check_seen' in fields:
    #         record_ids = self.search([('id', 'in', self._ids), ('state', '=', 'draft')])
    #         if record_ids:
    #             records = self.browse(record_ids)
    #             records.write({'state': 'seen'})
    #         for r in res:
    #             if r['state'] == 'draft':
    #                 res[res.index(r)]['state'] = 'seen'
    #     return res

    @api.multi
    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise UserError(_('Can not delete record in state different draft'))
        return super(QuotationRequest, self).unlink()

class QuotationRequestDetail(models.Model):
    _name = 'quotation.request.detail'
    _description = 'Quotation request detail'

    req_quotation_id = fields.Many2one('quotation.request')
    sequence = fields.Char(string='Sequence', readonly=True, copy=False)
    name = fields.Char()
    price = fields.Float()
    cus_confirm = fields.Boolean('Customer confirm')
    ref_id = fields.Integer()
