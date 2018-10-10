#!/usr/bin/python
# -*- encoding: utf-8 -*-

from odoo import fields,models,api, _
import datetime
import requests
import json
from unidecode import unidecode
from datetime import timedelta
from odoo.tools.safe_eval import safe_eval


class BtekAutoSendLogDetail(models.Model):
    _name = 'btek.auto.send.log.detail'
    _description = 'Btek Auto Send Messages Log Detail'

    name = fields.Char(readonly=True)
    btek_auto_send_log_id = fields.Many2one('btek.auto.send.log', readonly=True)
    create_day = fields.Datetime(string='Day Sent', readonly=True)
    result = fields.Selection([('sent', 'Sent'), ('fail', 'Fail')], readonly=True)


class BtekAutoSendLog(models.Model):
    _name = 'btek.auto.send.log'
    _description = 'Btek Auto Send Messages Log'
    _rec_name = 'create_day'

    btek_auto_send_id = fields.Many2one('btek.auto.send', readonly=True)
    btek_auto_send_mail_id = fields.Many2one('btek.auto.send.mail', readonly=True)
    create_day = fields.Datetime(string='Day Sent', readonly=True)
    total_message = fields.Integer(readonly=True)
    note = fields.Text(readonly=True)
    btek_auto_send_log_detail_ids = fields.One2many('btek.auto.send.log.detail', 'btek_auto_send_log_id', readonly=True)



class BtekAutoSend(models.Model):
    _name = 'btek.auto.send'
    _description = 'Btek Auto Send'
    _inherits = {'ir.cron': "ir_cron_id"}
    _rec_name = 'subject'

    _model_id = [('res.partner', _('Customer'))]

    def _default_template(self):
        channel = self.channel
        if not channel:
            channel = 'sms'
        external_id_dict = {'sms': 'btek_marketing.btek_sms_template',
                            'zalo': 'btek_marketing.btek_zalo_template',
                            'viber': 'btek_marketing.btek_viber_template',
                            'facebook': 'btek_marketing.btek_facebook_template',
                            'mobile_push': 'btek_marketing.btek_mobile_push_template'}
        external_id = external_id_dict.get(channel)
        return self.env.ref(external_id).id

    channel = fields.Selection([('sms', 'SMS'),
                                ('zalo', 'Zalo'),
                                ('viber', 'Viber'),
                                ('facebook', 'Facebook'),
                                ('mobile_push', 'Mobile push')], default='sms')
    subject = fields.Char()
    active = fields.Boolean(default=True)

    # message
    brand_name = fields.Many2one('btek.sms.config')
    sms_type = fields.Selection(
        [('1', 'Brandname dvertisement'), ('2', 'Brandname Customer Care'),
         ('3', 'Random numbers'), ('4', 'Fixed Number Notify'),
         ('6', 'Fixed number Verify'), ('7', 'OPT'),
         ('8', 'Fixed Number 10 Numbers'), ('13', 'Two-way message')],
        related='brand_name.sms_type', readonly=True)
    accent_vietnamese = fields.Selection(
        [('no_accent', 'No accent'), ('accent', 'Accent')],
        default='no_accent')
    zalo_url_id = fields.Many2one('btek.zalo.config')
    model_id = fields.Selection(selection=_model_id, string='Model', default='res.partner', required=True)
    btek_auto_condition_ids = fields.One2many('btek.auto.condition', 'btek_auto_send_id')
    define_domain = fields.Char(compute='_compute_define_domain',
                                string='Domain', default=[])
    domain = fields.Text(default='[]')
    auto_domain = fields.Char(compute='_compute_auto_domain', string='Domain total', default=[], readonly=True)
    message_template_id = fields.Many2one('btek.message.template', default=_default_template)
    message = fields.Char()
    state = fields.Selection([('draft', 'Draft'), ('running', 'Running')],
                             string='Status', required=True, readonly=True,
                             copy=False, default='draft')
    btek_auto_send_log_ids = fields.One2many('btek.auto.send.log', 'btek_auto_send_id')

    @api.onchange('channel')
    def _change_channel(self):
        channel = self.channel
        external_id_dict = {'sms': 'btek_marketing.btek_sms_template',
                            'zalo': 'btek_marketing.btek_zalo_template',
                            'viber': 'btek_marketing.btek_viber_template',
                            'facebook': 'btek_marketing.btek_facebook_template',
                            'mobile_push': 'btek_marketing.btek_mobile_push_template'}
        external_id = external_id_dict.get(channel)
        self.message_template_id = self.env.ref(external_id).id

    @api.onchange('message_template_id')
    def _message_template_change(self):
        self.message = self.message_template_id.message

    @api.multi
    def action_confirm(self):
        args = []
        args.append(self.id)
        self.write({'model': 'btek.auto.send', 'function': 'process_send_message', 'args': args, 'state': 'running'})

    @api.multi
    def action_cancel(self):
        self.write({'model': False, 'function': False, 'args': False, 'state': 'draft'})

    @api.multi
    @api.depends('btek_auto_condition_ids')
    def _compute_define_domain(self):
        for s in self:
            date_time_now = datetime.datetime.now()
            current_day = date_time_now.strftime('%Y-%m-%d')
            current_month_day = date_time_now.strftime('%m-%d')
            current_year = str(date_time_now.year)
            current_month = str(date_time_now.month)
            date_dict = {
                'current_day': current_day,
                'current_month_day': current_month_day,
                'current_year': current_year,
                'current_month': current_month}
            define_domain = []
            if s.btek_auto_condition_ids:
                for condition in s.btek_auto_condition_ids:
                    if condition.option_date_define:
                        if condition.numbers_days:
                            numbers_days_before = (
                            date_time_now + timedelta(days=-condition.numbers_days)).strftime('%Y-%m-%d')
                            date_dict['numbers_days_before'] = numbers_days_before
                            numbers_days_after = (
                            date_time_now + timedelta(days=condition.numbers_days)).strftime('%Y-%m-%d')
                            date_dict['numbers_days_after'] = numbers_days_after
                            domain = [condition.name, condition.operator, date_dict.get(condition.value_compare)]
                            define_domain.append(domain)
                        else:
                            domain = [condition.name, condition.operator,
                                      date_dict.get(condition.value_compare)]
                            define_domain.append(domain)
            s.define_domain = str(define_domain)

    @api.multi
    @api.depends('define_domain', 'domain')
    def _compute_auto_domain(self):
        for s in self:
            auto_domain = eval(s.define_domain) + eval(s.domain)
            s.auto_domain = auto_domain

    def get_recipients(self):
        if self.auto_domain:
            domain = safe_eval(self.auto_domain)
            contact_list = self.env[self.model_id].search(domain)
        return contact_list

    def run_manually(self):
        return self[0].ir_cron_id.method_direct_trigger()

    def send_sms_auto(self, url, ary_ordered_names, brand_name, api_key, secret_key, sms_type, content, mobiles):
        values = {'ApiKey': api_key,
                  'SecretKey': secret_key,
                  'Phone': mobiles,
                  'Content': content,
                  'SmsType': sms_type}
        if brand_name:
            values['Brandname'] = brand_name
        getdata = "&".join(
            [item + '=' + (values[item]) for item in ary_ordered_names])
        url_send = url + getdata
        if requests:
            try:
                response_string = requests.get(url_send)
                if response_string:
                    content = json.loads(response_string.content)
                    if int(content['CodeResult']) == 100:
                        return content['SMSID']
                    else:
                        return False
            except Exception:
                return False
            return response_string

    def send_zalo_auto(self, url, spCode, userId, message):
        headers = {'Content-type': 'application/json'}
        data = {'spCode': spCode, "message": message, "userId": userId}
        data = json.dumps(data)
        if requests:
            try:
                response = requests.post(url, data=data, headers=headers)
            except requests.exceptions.RequestException as e:
                return False
        return response

    @api.multi
    def process_send_message(self, ids):
        for s in self.browse(ids):
            contact_list = s.get_recipients()
            create_day = datetime.datetime.now()
            total_message = 0
            if contact_list:
                if s.channel == 'zalo':
                    config = s.env['btek.zalo.config'].search([])
                    url = config.url + '/message-text'
                    spCode = config.spcode
                    message = s.message
                    line_ids = []
                    for contact in contact_list:
                        if contact.zalo_id:
                            total_message += 1
                            userId = contact.zalo_id
                            try:
                                response = s.send_zalo_auto(url=url, spCode=spCode, userId=userId, message=message)
                                if response:
                                    line_ids.append((0, 0,{'name': contact.name, 'create_day': create_day, 'result': 'sent'}))
                            except Exception:
                                continue
                    btek_auto_zalo_log = s.env['btek.auto.send.log'].create({
                        'create_day': create_day,
                        'btek_auto_send_id': s.id,
                        'total_message': total_message,
                        'btek_auto_send_log_detail_ids': line_ids})

                elif s.channel == 'sms':
                    if s.brand_name.sms_supplier == 'eSMS':
                        api_key = s.brand_name.api_key
                        secret_key = s.brand_name.secret_key
                        sms_type = s.brand_name.sms_type
                        if s.accent_vietnamese == 'no_accent':
                            content = unidecode(s.message)
                        else:
                            content = s.message
                        mobile_list = []
                        for contact in contact_list:
                            if contact.mobile:
                                mobile_list.append(contact.mobile)
                        mobiles = ",".join(mobile for mobile in mobile_list)
                        total_message = len(mobile_list)
                        ary_ordered_names = []
                        ary_ordered_names.append('Phone')
                        ary_ordered_names.append('ApiKey')
                        ary_ordered_names.append('SecretKey')
                        ary_ordered_names.append('Content')
                        if s.brand_name.name:
                            brand_name = s.brand_name.name
                            ary_ordered_names.append('Brandname')
                        else:
                            brand_name = False
                        ary_ordered_names.append('SmsType')
                        url = s.brand_name.url + '/SendMultipleMessage_V4_get?'
                        sms_result = s.send_sms_auto(url, ary_ordered_names, brand_name, api_key, secret_key, sms_type, content, mobiles)
                        if sms_result:
                            line_ids = []
                            for contact in contact_list:
                                if contact.mobile:
                                    line_ids.append((0, 0, {'name': contact.name, 'create_day': create_day, 'result': 'sent'}))
                            btek_auto_zalo_log = s.env[
                                'btek.auto.send.log'].create({
                                'create_day': create_day,
                                'btek_auto_send_id': s.id,
                                'total_message': total_message,
                                'btek_auto_send_log_detail_ids': line_ids})
            else:
                btek_auto_zalo_log = s.env[
                    'btek.auto.send.log'].create({
                    'create_day': create_day,
                    'btek_auto_send_id': s.id,
                    'total_message': total_message,
                    'note': 'No customer must be send message in schedule'})
        return True


class IrModelFields(models.Model):
    _inherit= 'ir.model.fields'

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        # print 'co chay qua khong'
        # raise
        # print 'co chay qua khong'
        #                   'chỉnh sửa lại nội dung cho phù hợp'))
        return super(IrModelFields, self).search(args, offset=offset,
                                                      limit=limit, order=order,
                                                      count=count)
