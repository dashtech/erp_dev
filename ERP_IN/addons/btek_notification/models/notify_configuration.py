# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError
import datetime, requests, json
import string, random
from odoo import SUPERUSER_ID


class priority_chanel_send_message_line(models.Model):
    _name = 'priority.chanel.send.message.line'
    _order = 'sequence'

    priority_id = fields.Many2one(
        'priority.chanel.send.message', 'Priority',
        required=True, ondelete='cascade')
    sequence = fields.Integer()
    chanel = fields.Selection([
        ('app', 'App'),
        ('sms', 'Sms'),
        ('email', 'Email')
    ], required=True)

    _sql_constraints = [
        ('priority_sequence_chanel_uniq',
         'unique(priority_id,sequence,chanel)',
         'Priority chanel send message wrong, \nsequence, chanel must be per user!')
    ]

    def get_chanel_selection(self):
        uid = self.env.uid
        user = self.env['res.users'].browse(uid)

        selection_field = \
            self.with_context(lang=user.partner_id.lang
                              )._fields['chanel']
        selection = selection_field.selection
        return selection


class priority_chanel_send_message(models.Model):
    _name = 'priority.chanel.send.message'

    user_id = fields.Many2one('res.users', 'User',
                              required=True)
    line_ids = fields.One2many(
        'priority.chanel.send.message.line',
        'priority_id', 'Lines', required=True)

    _sql_constraints = [
        ('user_uniq', 'unique(user_id)',
         'User already exists!')
    ]

    @api.model
    def default_get(self, fieldlist):
        res = super(priority_chanel_send_message, self).default_get(
            fieldlist) or {}
        res['line_ids'] = []
        index = 10
        for item in self.env['priority.chanel.send.message.line'
        ].get_chanel_selection():
            res['line_ids'].append(
                (0, 0, {'sequence': index, 'chanel': item[0]})
            )
            index += 10

        return res


class notify_blacklist(models.Model):
    _name = 'notify.blacklist'

    user_id = fields.Many2one('res.users', 'User',
                              required=True)
    configuration_id = fields.Many2one('notify.model.configuration',
                                       'Configuration')

    _sql_constraints = [
        ('configuration_user_uniq', 'unique(user_id,configuration_id)',
         'Configuration, user must be unique!')
    ]


class send_notify_message_log(models.Model):
    _name = 'send.notify.message.log'
    _order = 'create_date desc'

    message_ids = fields.Many2many(
        'notify.message', 'notify_message_message_log',
        'log_id', 'message_id', 'Messages', readonly=True)
    datas = fields.Text(readonly=True)
    send_error = fields.Text(readonly=True)
    result = fields.Char(readonly=True)
    result_error = fields.Text(readonly=True)


class notify_message_result(models.Model):
    _name = 'notify.message.result'
    _order = 'create_date desc'

    message_id = fields.Many2one('notify.message', 'Message',
                                 required=True)
    user_id = fields.Many2one('res.users', 'User')
    partner_id = fields.Many2one('res.partner', 'Partner',
                                 reuqired=True)
    state = fields.Selection([('fail', 'Fail'),
                              ('success', 'Success')],
                             required=True)
    reason = fields.Char()

    @api.model
    def create(self, vals):
        if vals.get('user_id', False) and not vals.get('partner_id', False):
            user = self.env['res.users'].browse(vals['user_id'])
            vals['partner_id'] = user.partner_id.id
        return super(notify_message_result, self).create(vals)

    @api.multi
    @api.constrains('message_id', 'partner_id')
    def client_message_unique(self):
        for result in self:
            domain = [('message_id', '=', result.message_id.id),
                      ('partner_id', '=', result.partner_id.id),
                      ]
            duplicate_result = self.search(domain)
            if len(duplicate_result) > 1:
                return False
        return True


class notify_message(models.Model):
    _name = 'notify.message'
    _order = 'create_date desc'

    name = fields.Char(required=True)
    content = fields.Text(required=True)
    template_id = fields.Many2one('notify.message.template',
                                  'Template', required=True)
    configuration_id = fields.Many2one('notify.model.configuration',
                                       'Configuration', readonly=True)
    user_ids = fields.Many2many('res.users',
                                'notify_message_user_rel',
                                'message_id', 'user_id',
                                'Users')
    partner_ids = fields.Many2many('res.partner',
                                'notify_message_partner_rel',
                                'message_id', 'partner_id',
                                'Partners')
    result_ids = fields.One2many('notify.message.result',
                                 'message_id', 'Result', readonly=True)
    log_ids = fields.Many2many(
        'auditlog.log', 'notify_message_auditlog_log_rel',
        'notify_message_id', 'auditlog_log_id',
        'Logs', readonly=True
    )
    log_line_ids = fields.Many2many(
        'auditlog.log.line', 'notify_message_auditlog_log_line_rel',
        'notify_message_id', 'auditlog_log_line_id',
        'Log lines', readonly=True
    )
    fail_reason = fields.Char()
    state = fields.Selection([('draft', 'Draft'),
                              ('sending', 'Sending'),
                              ('sent', 'Sent'),
                              ('fail', 'Fail'),
                              ('cancel', 'Cancel')],
                             default='draft')
    sequence = fields.Char('Extend ID', readonly=True)
    open_url = fields.Char(compute='_compute_open_url')
    callback_token = fields.Char()
    callback_url = fields.Char(compute='_compute_callback_url')

    @api.model
    def create(self, vals):
        res = super(notify_message, self).create(vals)

        token = ''.join(
            random.choice(string.ascii_letters) for x in range(random.randint(10, 20)))
        callback_token = '{}/{}'.format(token, res.id)
        res.write({'callback_token': callback_token})
        return res

    @api.multi
    def _compute_callback_url(self):
        base_url = self.env['ir.config_parameter'
        ].get_param('web.base.url', '')
        for message in self:
            message.callback_url = \
                '{}/update-message-to-mobile-state/{}/'.format(
                    base_url, message.callback_token)

    @api.multi
    def _compute_open_url(self):
        for message in self:
            if not message.configuration_id.open_url:
                message.open_url = ''
                continue
            if not message.log_ids:
                message.open_url = ''
                continue
            message.open_url = message.configuration_id.open_url.format(self.log_ids[0].res_id)

    @api.multi
    def name_get(self):
        res = []
        for message in self:
            res.append((message.id, u'{}({})'.format(message.name, message.id)))
        return res

    @api.multi
    def action_cancel(self):
        self.ensure_one()
        if self.state != 'draft':
            return True

        return self.write({
            'state': 'cancel'
        })

    @api.multi
    def action_sending(self):
        for message in self:
            if message.state != 'draft':
                continue
            message.write({'state': 'sending'})
        return True

    @api.multi
    def action_resend(self):
        for message in self:
            if message.state != 'fail':
                continue
            message.write({'state': 'draft'})
        return True

    @api.multi
    def action_done(self):
        for message in self:
            if message.state != 'sending':
                continue
            message.write({'state': 'sent'})
        return True

    @api.multi
    def action_fail(self):
        for message in self:
            if message.state != 'sending':
                continue
            message.write({'state': 'fail'})
        return True

    @api.multi
    def get_data_to_send(self):
        self.ensure_one()
        user_infos = []
        for user in self.user_ids:
            user_info = user.get_info_to_notify_message()

            if not user_info:
                continue

            user_info['callback_url'] = u'{}u/{}'.format(self.callback_url,
                                                         user.id)
            user_infos.append(
                user_info
            )
        partner_infos = []
        for partner in self.partner_ids:
            partner_info = partner.get_info_to_notify_message()

            if not partner_info:
                continue

            partner_info['callback_url'] = u'{}/p/{}'.format(self.callback_url,
                                                             partner.id)
            partner_infos.append(partner_info)

        data = {
            'id': self.id,
            'data_object': self.configuration_id.model_id.model,
            'data_name': self.configuration_id.model_id.name,
            'data_ref_ids': self.log_ids.mapped('res_id'),
            'action': self.configuration_id.action_code or '',
            'open_url': self.open_url,
            'addition_data': self.configuration_id.name,
            'message': self.content,
            'domain': u'{}'.format(self.env.cr.dbname),
            'users': user_infos,
            'partners': partner_infos,
            'mobile': self.env['res.users'].browse(SUPERUSER_ID).mobile or '',
        }
        return data

    @api.model
    def find_to_send_message(self):
        messages = self.search(
            [('state', '=', 'draft'),('sequence', '=', False)])
        if not messages:
            return False

        messages.send_message()
        return True

    @api.multi
    def send_message(self):
        datas = []
        for message in self:
            data = message.get_data_to_send()
            datas.append(data)

        general_config = self.env['general.notify.configuration'].get_info()

        url_post = general_config.url
        header_authorization = general_config.header_authorization

        data_to_post = datas
        data_to_post = json.dumps(data_to_post)
        headers = {'Authorization': header_authorization,
                   'Content-Type': 'application/json'
                   }

        log_value = {
            'message_ids': [(6, False, self._ids)],
            'datas': data_to_post,
        }
        log = self.env['send.notify.message.log'].create(log_value)

        try:
            response = requests.post(url_post, data_to_post, headers=headers)
        except Exception as e:
            log.write({
                'send_error': unicode(e)
            })

        try:
            result = response.text
            log.write({
                'result': unicode(result)
            })
            self.process_send_result(result)
        except Exception as e:
            log.write({
                'result_error': unicode(e)
            })
        return True

    def process_send_result(self, result):
        res = json.loads(result)

        result = res.get("result", {})
        if not result:
            return True

        for message in self:
            sequence = result.get(str(message.id), False)
            if not sequence:
                continue
            message.write({
                'sequence': unicode(sequence)
            })
            message.action_sending()
        return True


class notify_message_template(models.Model):
    _name = 'notify.message.template'
    _inherits = {'ir.ui.view': 'view_id'}

    view_id = fields.Many2one('ir.ui.view',
                              'View', required=True)
    content = fields.Text()

    def set_arch_base(self):
        self.ensure_one()
        content = u"""<?xml version="1.0"?>
        <t name="1" t-name="1">
                    {}</t>""".format(self.content)
        super(notify_message_template, self).write({
            'arch_base': content
        })

    @api.model
    def create(self,vals):
        res = super(notify_message_template, self).create(vals)
        res.set_arch_base()
        return res

    @api.multi
    def write(self, vals):
        res = super(notify_message_template, self).write(vals)
        self.set_arch_base()
        return res


class notify_model_configuration_line(models.Model):
    _name = 'notify.model.configuration.line'
    _order = 'sequence'

    configuration_id = fields.Many2one('notify.model.configuration',
                                       'Configuration', required=True,
                                       ondelete='cascade')
    andor = fields.Selection([('and', 'And'),
                              ('or', 'Or')], required=True,
                             default='and')
    sequence = fields.Integer()
    field_id = fields.Many2one('ir.model.fields', 'Field',
                               required=True)
    old_value = fields.Char()
    new_value = fields.Char()


class notify_model_configuration(models.Model):
    _name = 'notify.model.configuration'

    name = fields.Char(required=True)
    action = fields.Selection([('create', 'Create'),
                               ('write', 'Update'),
                               ('unlink', 'Delete')],
                              default='write', required=True)
    action_code = fields.Char(required=True)
    open_url = fields.Char()
    line_ids = fields.One2many('notify.model.configuration.line',
                               'configuration_id',
                               'Lines', required=True)
    model_id = fields.Many2one('ir.model', 'Model', required=True)
    template_id = fields.Many2one('notify.message.template',
                                  'Template', required=True,
                                  ondelete='set null')
    state = fields.Selection([('draft', 'Draft'),
                              ('active', 'Active')],
                             required=True, default='draft')
    group_ids = fields.Many2many('res.groups',
                                 'notify_model_configuration_group_rel',
                                 'configuration_id', 'group_id',
                                 string='Groups')
    partner_field = fields.Many2many('ir.model.fields')
    message_ids = fields.One2many('notify.message', 'configuration_id',
                                  string='Messages', readonly=True)
    blacklist = fields.Many2many('res.users', 'notify_blacklist',
                                 'configuration_id', 'user_id',
                                 string='Black list', readonly=True)
    last_run = fields.Datetime(
        default=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    config_notify_to_partner = fields.Boolean(
        compute='_compute_config_notify_to_partner')

    @api.model
    def default_get(self, fields):
        res = super(notify_model_configuration, self).default_get(fields)
        config = self.env['general.notify.configuration'].get_info()
        res['config_notify_to_partner'] = config.notify_to_partner
        return res

    @api.multi
    def _compute_config_notify_to_partner(self):
        config_notify_to_partner = \
            self.default_get([]).get(
                'config_notify_to_partner', False)
        for config in self:
            config.config_notify_to_partner = config_notify_to_partner


    @api.multi
    def action_inactive(self):
        return self.write({'state': 'draft'})

    @api.multi
    def action_active(self):
        return self.write({'state': 'active'})

    def build_where_condition(self):
        datenow = datetime.datetime.now() + datetime.timedelta(minutes=-2)
        end_date = datenow.strftime('%Y-%m-%d %H:%M:%S')

        date_condition = u" and l.create_date <= '{}'".format(end_date)
        if self.last_run:
            date_condition = u"{} and l.create_date > '{}'".format(
                date_condition, self.last_run)

        if not self.line_ids:
            self.write({
                'last_run': end_date,
            })
            return date_condition

        res = u' {} and ('.format(date_condition)
        for line in self.line_ids:
            old_value_condition = line.old_value and u"and ll.old_value_text = '{}'".format(line.old_value) or ''
            new_value_condition = line.new_value and u"and ll.new_value_text = '{}'".format(line.new_value) or ''
            res_line = u'{} (ll.field_id = {} {} {})'.format(
                line.andor,
                line.field_id.id,
                old_value_condition,
                new_value_condition
            )
            res = u'''{} {}'''.format(res, res_line)
        res = u'{} )'.format(res).replace('( and', '(').format(res).replace('( or', '(')
        self.write({
            'last_run': end_date,
        })
        return res

    def find_log(self):
        where_condition = self.build_where_condition()

        querry = """
                    select l.id, ll.id
                    from auditlog_log_line as ll
                      left join auditlog_log as l
                      on l.id = ll.log_id
                    where l.model_id = {}
                      and l.method = '{}'
                      {}
                """.format(self.model_id.id,
                           self.action,
                           where_condition)

        self.env.cr.execute(querry)
        log_ids = []
        log_line_ids = []
        for row in self.env.cr.fetchall():
            if row[0] not in log_ids:
                log_ids.append(row[0])

            if row[1] not in log_line_ids:
                log_line_ids.append(row[1])

        return log_ids, log_line_ids

    def find_blacklist(self):
        blacklist_user_ids = []

        global_blacklists = self.env['notify.blacklist'].search([
            ('configuration_id', '=', False)
        ])
        global_blacklist_user_ids = \
            [global_blacklist.user_id.id for global_blacklist in global_blacklists]

        local_blacklist_user_ids = self.blacklist._ids

        blacklist_user_ids.extend(global_blacklist_user_ids)
        blacklist_user_ids.extend(local_blacklist_user_ids)
        return blacklist_user_ids

    def find_to_user(self):
        if not self.group_ids:
            return []

        blacklist_user_ids = self.find_blacklist()
        domain = []
        if len(self.group_ids) > 1:
            domain = ['|' for i in range(0, len(self.group_ids)-1)]

        for group in self.group_ids:
            domain.append(('groups_id', 'in', group.id))

        user_s = self.env['res.users'].search(domain)
        user_ids = \
            [user.id for user in user_s if user.id not in blacklist_user_ids]
        return user_ids

    def find_to_partner(self, logs, sub_log_lines):
        config = self.env['general.notify.configuration'].get_info()
        if not config.notify_to_partner:
            return []

        if not self.partner_field:
            return []
        res = []
        for partner_f in self.partner_field:
            res_ids = [log.res_id for log in logs]
            res_objs = self.env[logs[0].model_id.model].browse(res_ids)

            try:
                if partner_f.ttype == 'many2one':
                    res.append(res_objs.mapped(partner_f.name).id)
                    continue
                else:
                    res.extend(res_objs.mapped(partner_f.name)._ids)
            except:
                pass

        return res

    def generate_message(self, logs, log_lines):
        values = {
            'logs': logs,
            'log_lines': log_lines,
            'records': self.env[self.model_id.model].browse([log.res_id for log in logs]),
                  }
        view = self.template_id.view_id

        try:
            content = view.render(
                values=values).strip()
        except Exception as e:
            raise UserError(
                _('Template message error:\n{}').format(unicode(e))
            )

        return content

    @api.multi
    def run(self):
        self.ensure_one()

        log_ids, log_line_ids = self.find_log()

        if not log_line_ids or not log_ids:
            return {'result': 'error',
                    'messgae': 'Error: Can not find any logs that match the conditions below!'}

        user_ids = self.find_to_user()

        logs = self.env['auditlog.log'].browse(log_ids)
        log_lines = self.env['auditlog.log.line'].browse(log_line_ids)

        log_line_dict = {}
        for log_line in log_lines:
            if not log_line_dict.get(log_line.log_id.id, False):
                log_line_dict[log_line.log_id.id] = []
            log_line_dict[log_line.log_id.id].append(log_line.id)

        message_values = []

        for log in logs:
            sub_log_line_ids = log_line_dict.get(log.id, [])
            sub_log_lines = self.env['auditlog.log.line'].browse(sub_log_line_ids)
            content = self.generate_message([log], sub_log_lines)

            partner_ids = self.find_to_partner([log], sub_log_lines)

            if not user_ids and not partner_ids:
                continue

            message_value = {
                'name': self.template_id.name,
                'template_id': self.template_id.id,
                'content': content,
                'user_ids': [(6, False, user_ids)],
                'partner_ids': [(6, False, partner_ids)],
                'log_ids': [(6, False, [log.id])],
                'log_line_ids': [(6, False, sub_log_line_ids)],
            }
            message_values.append((0, 0, message_value))

        self.write({
            'message_ids': message_values
        })

        return True

    def run_and_send(self):
        configs = self.search([('state', '=', 'active')])
        for config in configs:
            config.run()

        self.env['notify.message'].find_to_send_message()

        return True


class general_notify_configuration(models.Model):
    _name = 'general.notify.configuration'

    url = fields.Char()
    header_authorization = fields.Char()
    notify_to_partner = fields.Boolean(default=False)

    @api.model
    def get_info(self):
        return self.env.ref('btek_notification.only_general_notify_configuration')


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def get_info_to_notify_message(self):
        self.ensure_one()
        info = {
            'name': self.name
        }

        priority =['sms', 'email']
        for chanel in priority:
            if chanel == 'sms':
                if not self.mobile:
                    continue
                info['address'] = [self.mobile]
                info['channel'] = 'sms'
                return info

            if chanel == 'email':
                if not self.email:
                    continue
                info['address'] = [self.email]
                info['channel'] = 'email'

                return info
        return False



