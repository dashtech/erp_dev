#!/usr/bin/python
# -*- encoding: utf-8 -*-

from odoo import fields,models,api, _
import datetime
from datetime import timedelta
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class BtekAutoSendMail(models.Model):
    _name = 'btek.auto.send.mail'
    _description = 'Btek Auto Send Mail'
    _inherits = {'ir.cron': "ir_cron_id"}
    _rec_name = "subject"

    _model_id = [('res.partner', _('Customer'))]
    subject = fields.Char(required=True)
    active = fields.Boolean(default=True)

    # mail
    email_from = fields.Char(string='From', required=True,
                             default=lambda self: self.env['mail.message']._get_default_from())
    body_html = fields.Html(string='Body', sanitize_attributes=False)
    attachment_ids = fields.Many2many('ir.attachment',
                                      'btek_auto_send_mail_ir_attachments_rel',
                                      'btek_auto_send_mail_id', 'attachment_id',
                                      string='Attachments')
    campaign_id = fields.Many2one('utm.campaign', string='Campaign',
                                  help="This name helps you tracking your different campaign efforts, e.g. Fall_Drive, Christmas_Special")
    # source_id = fields.Many2one('utm.source', string='Subject', required=True,
    #                             ondelete='cascade',
    #                             help="This is the link source, e.g. Search Engine, another domain, or name of email list")
    medium_id = fields.Many2one('utm.medium', string='Medium',
                                help="This is the delivery method, e.g. Postcard, Email, or Banner Ad",
                                default=lambda self: self.env.ref(
                                    'utm.utm_medium_email'))
    model_id = fields.Selection(selection=_model_id, string='Recipients Model',
                                default='res.partner', required=True)
    btek_auto_condition_ids = fields.One2many('btek.auto.condition',
                                              'btek_auto_send_id')
    define_domain = fields.Char(compute='_compute_define_domain',
                                string='Domain', default=[])
    domain = fields.Text(default='[]')
    auto_domain = fields.Char(compute='_compute_auto_domain',
                              string='Domain total', default=[], readonly=True)
    state = fields.Selection([('draft', 'Draft'), ('running', 'Running')],
                             string='Status', required=True, readonly=True,
                             copy=False, default='draft')
    btek_auto_send_log_ids = fields.One2many('btek.auto.send.log',
                                             'btek_auto_send_mail_id')

    @api.multi
    def action_confirm(self):
        args = []
        args.append(self.id)
        self.write(
            {'model': 'btek.auto.send.mail', 'function': 'process_send_email',
             'args': args, 'state': 'running'})

    @api.multi
    def action_cancel(self):
        self.write({'model': False, 'function': False, 'args': False,
                    'state': 'draft'})

    # @api.model
    # def name_create(self, name):
    #     """ _rec_name is source_id, creates a utm.source instead """
    #     mass_mailing = self.create({'subject': name})
    #     return mass_mailing.name_get()[0]

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
                                date_time_now + timedelta(
                                    days=-condition.numbers_days)).strftime(
                                '%Y-%m-%d')
                            date_dict[
                                'numbers_days_before'] = numbers_days_before
                            numbers_days_after = (
                                date_time_now + timedelta(
                                    days=condition.numbers_days)).strftime(
                                '%Y-%m-%d')
                            date_dict[
                                'numbers_days_after'] = numbers_days_after
                            domain = [condition.name, condition.operator,
                                      date_dict.get(condition.value_compare)]
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
            contact_list = self.env[self.model_id].search(domain).ids
        return contact_list

    def run_manually(self):
        return self[0].ir_cron_id.method_direct_trigger()

    def send_mail(self):
        author_id = self.env.user.partner_id.id
        for mailing in self:
            # instantiate an email composer + send emails
            res_ids = mailing.get_recipients()
            if not res_ids:
                break
            # Convert links in absolute URLs before the application of the shortener
            mailing.body_html = self.env['mail.template']._replace_local_links(mailing.body_html)

            composer_values = {
                'author_id': author_id,
                'attachment_ids': [(4, attachment.id) for attachment in mailing.attachment_ids],
                'body': mailing.convert_links()[mailing.id],
                'subject': mailing.subject,
                'model': mailing.model_id,
                'email_from': mailing.email_from,
                'record_name': False,
                'composition_mode': 'mass_mail',
            }

            composer = self.env['mail.compose.message'].with_context(active_ids=res_ids).create(composer_values)
            composer.with_context(active_ids=res_ids).send_mail(auto_commit=True)
        return True

    def convert_links(self):
        res = {}
        for mass_mailing in self:
            utm_mixin = mass_mailing
            html = mass_mailing.body_html if mass_mailing.body_html else ''

            vals = {}
            # vals = {'mass_mailing_id': mass_mailing.id} - error in db_server

            if utm_mixin.campaign_id:
                vals['campaign_id'] = utm_mixin.campaign_id.id
            # if utm_mixin.source_id:
            #     vals['source_id'] = utm_mixin.source_id.id
            if utm_mixin.medium_id:
                vals['medium_id'] = utm_mixin.medium_id.id

            res[mass_mailing.id] = self.env['link.tracker'].convert_links(html, vals, blacklist=['/unsubscribe_from_list'])

        return res

    @api.multi
    def process_send_email(self, ids):
        for s in self.browse(ids):
            contact_list = s.get_recipients()
            contact_object = s.env[s.model_id].browse(contact_list)
            create_day = datetime.datetime.now()
            total_message = 0
            if len(contact_list) > 0:
                line_ids = []
                result_mail = s.send_mail()
                if result_mail:
                    for contact in contact_object:
                        if contact.email:
                            total_message += 1
                            line_ids.append((0, 0, {'name': contact.name,
                                                    'create_day': create_day,
                                                    'result': 'sent'}))
                    btek_auto_mail_log = s.env['btek.auto.send.log'].create({
                        'create_day': create_day,
                        'btek_auto_send_mail_id': s.id,
                        'total_message': total_message,
                        'btek_auto_send_log_detail_ids': line_ids})
            else:
                btek_auto_zalo_log = s.env[
                    'btek.auto.send.log'].create({
                    'create_day': create_day,
                    'btek_auto_send_mail_id': s.id,
                    'total_message': total_message,
                    'note': 'No customer must be send email in schedule'})
        return True
