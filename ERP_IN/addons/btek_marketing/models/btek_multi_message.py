#!/usr/bin/python
# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import datetime
import json
import requests
from odoo.tools.safe_eval import safe_eval
from unidecode import unidecode


class BtekMessageTemplate(models.Model):
    _name = 'btek.message.template'
    _description = 'MessageTemplate'

    name = fields.Char()
    channel = fields.Selection([('sms', 'SMS'),
                                ('zalo', 'Zalo'),
                                ('viber', 'Viber'),
                                ('facebook', 'Facebook'),
                                ('mobile_push', 'Mobile push')], default='sms')
    message = fields.Char()


class BtekSmsLog(models.Model):
    _name = 'btek.sms.log'
    _description = 'Btek SMS log'

    btek_multi_message_id = fields.Many2one('btek.multi.message')
    name = fields.Char()
    mobile = fields.Char()
    zalo_id = fields.Char()
    result = fields.Boolean()
    reason = fields.Selection([('success', 'Sending success'),
                               ('fail', 'Sending fail'),
                               ('mobile_syntax', 'Mobile Syntax')])


class BtekMultiMessage(models.Model):
    _name = 'btek.multi.message'
    _description = 'Btek Multi Message'

    _message_model = [('res.partner', _('Customer')), ('mail.mass_mailing.contact', _('Mailing List'))]

    name = fields.Char()
    color = fields.Integer(related='mass_mailing_campaign_id.color',
                           string='Color Index')
    mass_mailing_campaign_id = fields.Many2one('mail.mass_mailing.campaign',
                                               string='Mass Mailing Campaign')
    brand_name = fields.Many2one('btek.sms.config')
    sms_type = fields.Selection([('1', 'Brandname dvertisement'), ('2', 'Brandname Customer Care'),
                                 ('3', 'Random numbers'), ('4', 'Fixed Number Notify'),
                                 ('6', 'Fixed number Verify'), ('7', 'OPT'),
                                 ('8', 'Fixed Number 10 Numbers'), ('13', 'Two-way message')], related='brand_name.sms_type', readonly=True)
    accent_vietnamese = fields.Selection([('no_accent', 'No accent'), ('accent', 'Accent')], default='no_accent')
    zalo_url_id = fields.Many2one('btek.zalo.config')
    channel = fields.Selection([('sms', 'SMS'),
                                ('zalo', 'Zalo'),
                                ('viber', 'Viber'),
                                ('facebook', 'Facebook'),
                                ('mobile_push', 'Mobile push')], default='sms')
    create_date = fields.Datetime(default=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), string='Creation Date')
    sent_date = fields.Datetime(string='Sent Date', oldname='date', copy=False)
    schedule_date = fields.Datetime(string='Schedule in the Future')
    # receive_people = fields.Selection([('customer', 'Customer'),
    #                                    ('contact_list', 'Contact List')])
    message_model = fields.Selection(selection=_message_model,
                                     string='Recipients Model', required=True,
                                     default='mail.mass_mailing.contact')
    message_domain = fields.Char(string='Domain', oldname='domain', default=[])
    contact_list_ids = fields.Many2many('mail.mass_mailing.list',
                                        'multi_message_mailing_list_rel',
                                        string='Contact Lists')
    message_template_id = fields.Many2one('btek.message.template')
    message = fields.Char()

    state = fields.Selection(
        [('draft', 'Draft'), ('in_queue', 'In Queue'),
         ('sending', 'Sending'), ('error', 'Error'),
         ('done', 'Sent')], string='Status', required=True, readonly=True,
        copy=False, default='draft')
    next_departure = fields.Datetime(compute="_compute_next_departure",
                                     string='Next Departure')

    active = fields.Boolean(default=True)
    sms_charge_person = fields.Integer(compute='_compute_sms_charge_person', store=True)
    sms_charge_total = fields.Integer(compute='_compute_sms_charge_total', store=True)
    total = fields.Integer(compute='_compute_total')
    message_success = fields.Integer()
    message_fail = fields.Integer()
    mobile_syntax = fields.Integer()
    multi_sms_log = fields.Char()
    SMSID = fields.Char(readonly=True)
    SMS_send_status = fields.Integer(default=0, readonly=True)
    # @api.model
    # def create(self, vals):
    #     if 'message_template_id' in vals.keys():
    #         del vals['message_template_id']
    #     # print vals
    #     return super(BtekMultiMessage, self).create(vals)

    @api.onchange('brand_name')
    def _sms_type_change(self):
        self.sms_type = self.brand_name.sms_type

    @api.onchange('message_template_id')
    def _message_template_change(self):
        self.message = self.message_template_id.message

    @api.onchange('state')
    def _error_log_change_by_state(self):
        if self.state not in ('draft', 'in_queue', 'sending', 'done'):
            self.multi_sms_log = False

    @api.multi
    def put_in_queue(self):
        self.write({'sent_date': fields.Datetime.now(), 'state': 'in_queue'})

    @api.multi
    def cancel_send_message(self):
        self.write({'state': 'draft'})

    @api.multi
    def re_send_message(self):
        self.write({'state': 'in_queue'})
        self.multi_sms_log = False

    # @api.multi
    # def view_success_message(self):
    #     if self.channel == 'sms':
    #         domain = [('btek_multi_message_id', '=', self.id), ('result', '=', True)]
    #         action = self.env.ref('btek_marketing.action_btek_sms_log_tree')
    #         action_read = action.read([])[0]
    #         action_read['domain'] = domain
    #         return action_read

    @api.onchange('message_model', 'contact_list_ids')
    def _onchange_model_and_list(self):
        if self.message_model == 'mail.mass_mailing.contact':
            if self.contact_list_ids:
                self.message_domain = "[('list_id', 'in', %s), ('opt_out', '=', False)]" % self.contact_list_ids.ids
            else:
                self.message_domain = "[('list_id', '=', False)]"
        elif 'opt_out' in self.env[self.message_model]._fields:
            self.message_domain = "[('opt_out', '=', False)]"
        else:
            self.message_domain = []

    def _compute_next_departure(self):
        cron_next_call = self.env.ref('btek_marketing.ir_cron_multi_message_queue').sudo().nextcall
        for multi_message in self:
            schedule_date = multi_message.schedule_date
            if schedule_date:
                if datetime.now() > fields.Datetime.from_string(schedule_date):
                    multi_message.next_departure = cron_next_call
                else:
                    multi_message.next_departure = schedule_date
            else:
                multi_message.next_departure = cron_next_call

    @api.multi
    @api.depends('message_model', 'contact_list_ids')
    def _compute_total(self):
        for multi_message in self:
            multi_message.total = len(multi_message.sudo().get_recipients())

    def get_recipients(self):
        if self.message_domain:
            domain = safe_eval(self.message_domain)
            # res_ids = self.env[self.message_model].search(domain).ids
            contact_list = self.env[self.message_model].search(domain)
        return contact_list

    @api.multi
    @api.depends('message', 'accent_vietnamese')
    def _compute_sms_charge_person(self):
        for s in self:
            if not s.message:
                s.sms_charge_person = 0
                continue
            if s.accent_vietnamese == 'no_accent':
                if len(s.message) <= 160:
                    s.sms_charge_person = 1
                elif len(s.message) <= 306:
                    s.sms_charge_person = 2
                elif len(s.message) <= 459:
                    s.sms_charge_person = 3
                elif len(s.message) <= 612:
                    s.sms_charge_person = 4
                elif len(s.message) <= 765:
                    s.sms_charge_person = 5
                else:
                    raise UserError(_('Nội dung tin nhắn vượt quá giới hạn, '
                                      'chỉnh sửa lại nội dung cho phù hợp'))
            elif s.accent_vietnamese == 'accent':
                if len(s.message) <= 70:
                    s.sms_charge_person = 1
                elif len(s.message) <= 134:
                    s.sms_charge_person = 2
                elif len(s.message) <= 201:
                    s.sms_charge_person = 3
                elif len(s.message) <= 268:
                    s.sms_charge_person = 4
                elif len(s.message) <= 335:
                    s.sms_charge_person = 5
                else:
                    raise UserError(_('Nội dung tin nhắn vượt quá giới hạn, '
                                      'chỉnh sửa lại nội dung cho phù hợp'))
            else:
                pass

    @api.multi
    @api.depends('sms_charge_person', 'message_model', 'contact_list_ids')
    def _compute_sms_charge_total(self):
        for s in self:
            s.sms_charge_total = s.sms_charge_person * s.total

    @api.multi
    def action_duplicate(self):
        self.ensure_one()
        multi_message_copy = self.copy()
        if multi_message_copy:
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'btek.multi.message',
                'res_id': multi_message_copy.id,
                'context': self.env.context,
                'flags': {'initial_mode': 'edit'},
            }
        return False

    # send sms mesage
    def send_sms(self):
        if self.channel == 'sms' and self.brand_name.sms_supplier == 'eSMS':
            api_key = self.brand_name.api_key
            secret_key = self.brand_name.secret_key
            sms_type = self.brand_name.sms_type
            if self.accent_vietnamese == 'no_accent':
                content = unidecode(self.message)
            else:
                content = self.message
            contact_list = self.get_recipients()
            mobile_list = []
            for contact in contact_list:
                if contact.mobile:
                    mobile_list.append(contact.mobile)
            mobiles = ",".join(mobile for mobile in mobile_list)
            values = {'ApiKey': api_key,
                      'SecretKey': secret_key,
                      'Phone': mobiles,
                      'Content': content,
                      'SmsType': sms_type}
            ary_ordered_names = []
            ary_ordered_names.append('Phone')
            ary_ordered_names.append('ApiKey')
            ary_ordered_names.append('SecretKey')
            ary_ordered_names.append('Content')

            if self.brand_name.name:
                brand_name = self.brand_name.name
                values['Brandname'] = brand_name
                ary_ordered_names.append('Brandname')
            ary_ordered_names.append('SmsType')
            getdata = "&".join([item + '=' + (values[item]) for item in ary_ordered_names])
            url_send = self.brand_name.url + '/SendMultipleMessage_V4_get?' + getdata

            if requests:
                try:
                    response_string = requests.get(url_send)
                    if response_string:
                        code = eval(response_string.text.encode('utf-8'))
                        if int(code['CodeResult']) == 100:
                            return code['SMSID']
                        else:
                            self.multi_sms_log = _('CodeResult') + ' = ' + code['CodeResult'] + ': ' + code['ErrorMessage']
                            return False
                except requests.exceptions.RequestException as e:
                    self.multi_sms_log = str(e)
                    return False
            # multi_message.state = 'done'
        return True

    def get_send_sms_status(self):
        if self.channel == 'sms' and self.brand_name.sms_supplier == 'eSMS':
            api_key = self.brand_name.api_key
            secret_key = self.brand_name.secret_key
            RefId = self.SMSID
            values = {'ApiKey': api_key,
                      'SecretKey': secret_key,
                      'RefId': RefId}
            ary_ordered_names = []
            ary_ordered_names.append('RefId')
            ary_ordered_names.append('ApiKey')
            ary_ordered_names.append('SecretKey')
            getdata = "&".join([item + '=' + (values[item]) for item in ary_ordered_names])
            url_get_status = self.brand_name.url + '/GetSendStatus?' + getdata

            if requests:
                try:
                    response_string = requests.get(url_get_status)
                    if response_string:
                        code = eval(response_string.text.encode('utf-8'))
                        return code
                    else:
                        return False
                except requests.exceptions.RequestException as e:
                    return False

    def _check_mobile(self, mobile):
        if mobile:
            mobile_prefix = '84'
            if mobile.startswith("0"):
                mobile = mobile_prefix + mobile[1:].replace(" ",
                                                            "")
            elif mobile.startswith("+"):
                mobile = mobile.replace("+", "")
            else:
                mobile = mobile.replace(" ", "")
        return mobile

    @api.model
    def process_multi_sms_queue(self):
        multi_messages = self.search([('channel', '=', 'sms'),
                                      ('state', '=', 'in_queue'),
                                      '|', ('schedule_date', '<', fields.Datetime.now()), ('schedule_date', '=', False)])
        for multi_message in multi_messages:
                send_sms = multi_message.send_sms()
                if send_sms:
                    multi_message.SMSID = send_sms
                    multi_message.state = 'sending'
                else:
                    multi_message.state = 'error'
        return True

    def convert_mobile_start_zero(self, mobile):
        if mobile:
            mobile_prefix = '0'
            if mobile.startswith("+84"):
                mobile = mobile_prefix + mobile[3:].replace(" ", "")
            elif mobile.startswith("84"):
                mobile = mobile_prefix + mobile[2:].replace(" ", "")
            else:
                mobile = mobile.replace(" ", "")
        return mobile

    def get_receiver_list_sms(self):
        api_key = self.brand_name.api_key
        secret_key = self.brand_name.secret_key
        RefId = self.SMSID
        values = {'ApiKey': api_key,
                  'SecretKey': secret_key,
                  'RefId': RefId}
        ary_ordered_names = []
        ary_ordered_names.append('RefId')
        ary_ordered_names.append('ApiKey')
        ary_ordered_names.append('SecretKey')
        getdata = "&".join(
            [item + '=' + (values[item]) for item in ary_ordered_names])
        url_get_receiver = self.brand_name.url + '/GetSmsReceiverStatus_get?' + getdata
        if requests:
            try:
                response_string = requests.get(url_get_receiver)
                if response_string:
                    content = json.loads(response_string.content)
                    if content['CodeResult'] != 105:
                        receiver_list = content['ReceiverList']
                        return receiver_list
                    else:
                        return False
                else:
                    return False
            except requests.exceptions.RequestException as e:
                return False

    @api.model
    def process_check_sms_status(self):
        multi_messages = self.search([('state', '=', 'sending'), ('channel', '=', 'sms'), ('SMS_send_status', '!=', 5)])
        for multi_message in multi_messages:
            contact_list = multi_message.get_recipients()
            mobile_name_dict = {}
            for contact in contact_list:
                mobile_name_dict[multi_message.convert_mobile_start_zero(contact.mobile)] = contact.name
            contact_mobile_list = list(mobile_name_dict.keys())
            sms_status = multi_message.get_send_sms_status()
            if sms_status:
                multi_message.message_success = sms_status['SendSuccess']
                multi_message.message_fail = sms_status['SendFailed']
                multi_message.SMS_send_status = sms_status['SendStatus']
                if multi_message.SMS_send_status == 5:
                    multi_message.state = 'done'
                    receiver_list = multi_message.get_receiver_list_sms()
                    if receiver_list:
                        mobile_sent_list = [receiver['Phone'] for receiver in receiver_list]
                        contact_mobile_error = list(set(contact_mobile_list) - set(mobile_sent_list))
                        multi_message.mobile_syntax = len(contact_mobile_error)
                        for mobile_error in contact_mobile_error:
                            btek_sms_log = multi_message.env['btek.sms.log'].create({
                                'name': mobile_name_dict[mobile_error],
                                'mobile': mobile_error,
                                'btek_multi_message_id': multi_message.id,
                                'result': False,
                                'reason': 'mobile_syntax'
                            })
                        mobile_getway_error = []
                        mobile_success = []
                        for receivers in receiver_list:
                            if receivers['SentResult'] is True:
                                mobile_success.append(receivers['Phone'])
                            else:
                                mobile_getway_error(receivers['Phone'])
                        for mobile_succ in mobile_success:
                            btek_sms_log = multi_message.env['btek.sms.log'].create({
                                'name': mobile_name_dict[mobile_succ],
                                'mobile': mobile_succ,
                                'btek_multi_message_id': multi_message.id,
                                'result': True,
                                'reason': 'success'
                            })
                        for mobile_getway_err in mobile_getway_error:
                            btek_sms_log = multi_message.env['btek.sms.log'].create({
                                'name': mobile_name_dict[mobile_getway_err],
                                'mobile': mobile_getway_err,
                                'btek_multi_message_id': multi_message.id,
                                'result': False,
                                'reason': 'fail'
                            })
                elif multi_message.SMS_send_status == 4:
                    multi_message.state = 'error'
                else:
                    pass
        return True


# send zalo message
    def invite_zalo(self, url, spcode, message, lstPhoneNumbers):
        data = {'spCode': spcode, 'message': message, 'lstPhoneNumbers': lstPhoneNumbers}
        data = json.dumps(data)
        print data
        headers = {'Content-type': 'application/json'}
        if requests:
            try:
                response = requests.post(url, data=data, headers=headers)
            except requests.exceptions.RequestException as e:
                return e
        return response

    def get_total_follow(self, config, offset):
        url = config.url + '/follows'
        spcode = config.spcode
        data = {"spCode": spcode, "offset": offset, "count": 50}
        data = json.dumps(data)
        headers = {'Content-type': 'application/json'}
        if requests:
            try:
                response = requests.post(url, data=data, headers=headers)
                content = json.loads(response.content)
                total = content['result']['total']
            except requests.exceptions.RequestException as e:
                return False
        return total

    def get_zalo_id(self, url, spcode, phoneNumber):
        data = {'spCode': spcode, 'phoneNumber': phoneNumber}
        data = json.dumps(data)
        headers = {'Content-type': 'application/json'}
        if requests:
            try:
                response = requests.post(url, data=data, headers=headers)
            except requests.exceptions.RequestException as e:
                return e
        return response

    def send_zalo(self, url, spCode, userId, message):
        headers = {'Content-type': 'application/json'}
        data = {'spCode': spCode, "message": message, "userId": userId}
        data = json.dumps(data)
        if requests:
            try:
                response = requests.post(url, data=data, headers=headers)
            except requests.exceptions.RequestException as e:
                return e
        return response

    @api.model
    def process_invite_zalo(self):
        config = self.env['btek.zalo.config'].search([])
        domain = [('is_invite_zalo', '=', False)]
        partner_invite = self.env['res.partner'].search(domain)
        mailing_list = self.env['mail.mass_mailing.contact'].search(domain)
        url = config.url + '/message-invite'
        spcode = config.spcode
        message = 'Invite my app'
        mobile_list = []
        for p in partner_invite:
            if p.mobile:
                mobile_list.append(self._check_mobile(p.mobile))
                p.write({'is_invite_zalo': True})
        for m in mailing_list:
            if m.mobile:
                mobile_list.append(self._check_mobile(m.mobile))
                m.write({'is_invite_zalo': True})
        mobile_list = list(set(mobile_list))
        if len(mobile_list) > 0:
            response = self.invite_zalo(url=url, spcode=spcode, message=message, mobile_list=message)
        return True

    @api.model
    def process_get_zalo_id(self):
        config = self.env['btek.zalo.config'].search([])
        domain = [('zalo_id', '=', False), ('mobile', '!=', False), ('is_invite_zalo', '=', True)]
        partner_get_id = self.env['res.partner'].search(domain)
        mailling_get_id = self.env['mail.mass_mailing.contact'].search(domain)
        offset = config.total_follow
        total = self.get_total_follow(config=config, offset=offset)
        url = config.url + '/follow-profile'
        if total > 0:
            config.sudo().write({'total_follow': total})
            for p in partner_get_id:
                try:
                    response = self.get_zalo_id(url=url, spcode=config.spcode, phoneNumber=self._check_mobile(p.mobile))
                    content = json.loads(response.content)
                    if content['result'] is not None:
                        userId = content['result']['userId']
                        p.sudo().write({'zalo_id': userId})
                except Exception:
                    continue
            for m in mailling_get_id:
                try:
                    response = self.get_zalo_id(url=url, spcode=config.spcode, phoneNumber=self._check_mobile(m.mobile))
                    content = json.loads(response.content)
                    if content['result'] is not None:
                        userId = content['result']['userId']
                        m.sudo().write({'zalo_id': userId})
                except Exception:
                    continue
        return True

    def process_multi_zalo_queue(self):
        multi_messages = self.search([('channel', '=', 'zalo'),
                                      ('state', '=', 'in_queue'),
                                      '|', ('schedule_date', '<', fields.Datetime.now()), ('schedule_date', '=', False)])

        config = self.env['btek.zalo.config'].search([])
        url = config.url + '/message-text'
        spCode = config.spcode
        for multi_zalo in multi_messages:
            multi_zalo.state = 'sending'
            message = multi_zalo.message
            contact_list = multi_zalo.get_recipients()
            for contact in contact_list:
                if contact.zalo_id:
                    userId = contact.zalo_id
                    try:
                        response = multi_zalo.send_zalo(url=url, spCode=spCode, userId=userId, message=message)
                        content = json.loads(response.content)
                        if int(content['status']) == 0:
                            btek_sms_log = multi_zalo.env['btek.sms.log'].create({
                                'name': contact.name,
                                'mobile': contact.mobile,
                                'zalo_id': contact.zalo_id,
                                'btek_multi_message_id': multi_zalo.id,
                                'result': True,
                                'reason': 'success'
                            })
                        else:
                            btek_sms_log = multi_zalo.env['btek.sms.log'].create({
                                'name': contact.name,
                                'mobile': contact.mobile,
                                'zalo_id': contact.zalo_id,
                                'btek_multi_message_id': multi_zalo.id,
                                'result': False,
                                'reason': 'fail'
                            })
                    except Exception:
                        btek_sms_log = multi_zalo.env['btek.sms.log'].create({
                            'name': contact.name,
                            'mobile': contact.mobile,
                            'zalo_id': contact.zalo_id,
                            'btek_multi_message_id': multi_zalo.id,
                            'result': False,
                            'reason': 'fail'
                        })
                        continue
            multi_zalo.sudo().write({'message_success': multi_zalo.env['btek.sms.log'].search_count\
                ([('btek_multi_message_id', '=', multi_zalo.id), ('result', '=', True)])})
            multi_zalo.sudo().write(
                {'message_fail': multi_zalo.env['btek.sms.log'].search_count \
                    ([('btek_multi_message_id', '=', multi_zalo.id),
                      ('result', '=', False)])})
            multi_zalo.state = 'done'
        return True
