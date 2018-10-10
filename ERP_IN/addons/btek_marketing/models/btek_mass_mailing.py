#!/usr/bin/python
# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import json
import requests


# class btek_mass_mailing(models.Model):
#     _inherit = 'mail.mass_mailing'
#
#     chanel = fields.Selection([(1, _('Mail')), (2, 'Zalo'), (3, 'Viber'), (4, 'Facebook')], string='Chanel')
#     mailing_condition_ids = fields.One2many('btek.mass.mailing.condition', 'mass_mailing_id', string='mailing_condition_ids')
#
#     # locct override base sendmail function
#     def send_mail(self):
#         author_id = self.env.user.partner_id.id
#         for mailing in self:
#             # instantiate an email composer + send emails
#             res_ids = mailing.get_remaining_recipients()
#             if not res_ids:
#                 raise UserError(_('Please select recipients.'))
#             # locct add send message with chanel
#             if mailing.chanel == 2:
#                 url = "http://192.168.0.199:8080/services/ext/social/zalo/message-text"
#                 if self.env.user.partner_id.mobile:
#                     phone = self.env.user.partner_id.mobile
#                 else:
#                     phone = self.env.user.partner_id.phone
#                 sp_code = self.env.user.partner_id.company_id.id
#                 message = mailing.name
#                 user_id = self.env.user.partner_id.zalo_id
#                 data = {
#                     "spCode": sp_code,
#                     "message": message,
#                     "phoneNumber": phone,
#                     "userId": user_id
#
#                 }
#                 response = requests.post(url, data=data)
#                 mailing.state = 'done'
#                 return response
#             if mailing.chanel == 1 or not mailing.chanel:
#                 # if mailing.mailing_condition_ids:
#                 #     for r in mailing.mailing_condition_ids:
#                 # Convert links in absolute URLs before the application of the shortener
#                 mailing.body_html = self.env['mail.template']._replace_local_links(mailing.body_html)
#
#                 composer_values = {
#                     'author_id': author_id,
#                     'attachment_ids': [(4, attachment.id) for attachment in mailing.attachment_ids],
#                     'body': mailing.convert_links()[mailing.id],
#                     'subject': mailing.name,
#                     'model': mailing.mailing_model,
#                     'email_from': mailing.email_from,
#                     'record_name': False,
#                     'composition_mode': 'mass_mail',
#                     'mass_mailing_id': mailing.id,
#                     'mailing_list_ids': [(4, l.id) for l in mailing.contact_list_ids],
#                     'no_auto_thread': mailing.reply_to_mode != 'thread',
#                 }
#                 if mailing.reply_to_mode == 'email':
#                     composer_values['reply_to'] = mailing.reply_to
#
#                 composer = self.env['mail.compose.message'].with_context(active_ids=res_ids).create(composer_values)
#                 composer.with_context(active_ids=res_ids).send_mail(auto_commit=True)
#                 mailing.state = 'done'
#             return True


class BtekMassMailingCampaign(models.Model):
    _inherit = 'mail.mass_mailing.campaign'

    clicks_ratio = fields.Float(compute="_compute_clicks_ratio",
                                  string="Number of clicks")
    received_ratio = fields.Float(compute="_compute_statistics",
                                  string='Received Ratio')
    opened_ratio = fields.Float(compute="_compute_statistics",
                                string='Opened Ratio')
    replied_ratio = fields.Float(compute="_compute_statistics",
                                 string='Replied Ratio')
    bounced_ratio = fields.Float(compute="_compute_statistics",
                                 string='Bounced Ratio')

    multi_message_ids = fields.One2many('btek.multi.message', 'mass_mailing_campaign_id', string='Multi Messages')
    total_sms = fields.Integer(compute='_compute_static_sms')
    total_contact_sms = fields.Integer(compute='_compute_static_sms')
    sms_success = fields.Integer(compute='_compute_static_sms')
    sms_fail = fields.Integer(compute='_compute_static_sms')
    sms_invalid = fields.Integer(compute='_compute_static_sms')
    sms_success_ratio = fields.Float(compute='_compute_static_sms')
    sms_fail_ratio = fields.Float(compute='_compute_static_sms')
    sms_invalid_ratio = fields.Float(compute='_compute_static_sms')

    total_zalo = fields.Integer(compute='_compute_static_zalo')
    total_contact_zalo = fields.Integer(compute='_compute_static_zalo')
    zalo_success = fields.Integer(compute='_compute_static_zalo')
    zalo_fail = fields.Integer(compute='_compute_static_zalo')
    zalo_invalid = fields.Integer(compute='_compute_static_zalo')
    zalo_success_ratio = fields.Float(compute='_compute_static_zalo')
    zalo_fail_ratio = fields.Float(compute='_compute_static_zalo')
    zalo_invalid_ratio = fields.Float(compute='_compute_static_zalo')

    def _compute_clicks_ratio(self):
        self.env.cr.execute("""
            SELECT COUNT(DISTINCT(stats.id)) AS nb_mails, COUNT(DISTINCT(clicks.mail_stat_id)) AS nb_clicks, stats.mass_mailing_campaign_id AS id
            FROM mail_mail_statistics AS stats
            LEFT OUTER JOIN link_tracker_click AS clicks ON clicks.mail_stat_id = stats.id
            WHERE stats.mass_mailing_campaign_id IN %s
            GROUP BY stats.mass_mailing_campaign_id
        """, (tuple(self.ids), ))

        campaign_data = self.env.cr.dictfetchall()
        mapped_data = dict([(c['id'], 100 * c['nb_clicks'] / c['nb_mails']) for c in campaign_data])
        for campaign in self:
            campaign.clicks_ratio = mapped_data.get(campaign.id, 0)

    def _compute_statistics(self):
        """ Compute statistics of the mass mailing campaign """
        self.env.cr.execute("""
            SELECT
                c.id as campaign_id,
                COUNT(s.id) AS total,
                COUNT(CASE WHEN s.sent is not null THEN 1 ELSE null END) AS sent,
                COUNT(CASE WHEN s.scheduled is not null AND s.sent is null AND s.exception is null THEN 1 ELSE null END) AS scheduled,
                COUNT(CASE WHEN s.scheduled is not null AND s.sent is null AND s.exception is not null THEN 1 ELSE null END) AS failed,
                COUNT(CASE WHEN s.id is not null AND s.bounced is null THEN 1 ELSE null END) AS delivered,
                COUNT(CASE WHEN s.opened is not null THEN 1 ELSE null END) AS opened,
                COUNT(CASE WHEN s.replied is not null THEN 1 ELSE null END) AS replied ,
                COUNT(CASE WHEN s.bounced is not null THEN 1 ELSE null END) AS bounced
            FROM
                mail_mail_statistics s
            RIGHT JOIN
                mail_mass_mailing_campaign c
                ON (c.id = s.mass_mailing_campaign_id)
            WHERE
                c.id IN %s
            GROUP BY
                c.id
        """, (tuple(self.ids), ))

        for row in self.env.cr.dictfetchall():
            total = row['total'] or 1
            row['delivered'] = row['sent'] - row['bounced']
            row['received_ratio'] = round(100.0 * row['delivered'] / total, 2)
            row['opened_ratio'] = round(100.0 * row['opened'] / total, 2)
            row['replied_ratio'] = round(100.0 * row['replied'] / total, 2)
            row['bounced_ratio'] = round(100.0 * row['bounced'] / total, 2)
            self.browse(row.pop('campaign_id')).update(row)

    @api.multi
    def _compute_static_sms(self):
        for campaign in self:
            row = {}
            SMSs = [multi_message for multi_message in campaign.multi_message_ids if multi_message.channel == 'sms']
            row['total_sms'] = len(SMSs)
            total_contact_sms = 0
            sms_success = 0
            sms_fail = 0
            for sms in SMSs:
                total_contact_sms += sms.total
                sms_success += sms.message_success
                sms_fail += sms.message_fail
            sms_invalid = total_contact_sms - sms_success - sms_fail
            row['total_contact_sms'] = total_contact_sms
            row['sms_success'] = sms_success
            row['sms_fail'] = sms_fail
            row['sms_invalid'] = sms_invalid
            total = row['total_contact_sms'] or 1
            row['sms_success_ratio'] = round(100.0 * row['sms_success'] / total, 2)
            row['sms_fail_ratio'] = round(100.0 * row['sms_fail'] / total, 2)
            row['sms_invalid_ratio'] = round(100.0 * row['sms_invalid'] / total, 2)
            campaign.update(row)

    @api.multi
    def _compute_static_zalo(self):
        for campaign in self:
            row = {}
            ZALOs = [multi_message for multi_message in
                    campaign.multi_message_ids if
                    multi_message.channel == 'zalo']
            row['total_zalo'] = len(ZALOs)
            total_contact_zalo = 0
            zalo_success = 0
            zalo_fail = 0
            for zalo in ZALOs:
                total_contact_zalo += zalo.total
                zalo_success += zalo.message_success
                zalo_fail += zalo.message_fail
            zalo_invalid = total_contact_zalo - zalo_success - zalo_fail
            row['total_contact_zalo'] = total_contact_zalo
            row['zalo_success'] = zalo_success
            row['zalo_fail'] = zalo_fail
            row['zalo_invalid'] = zalo_invalid
            total = row['total_contact_zalo'] or 1
            row['zalo_success_ratio'] = round(
                100.0 * row['zalo_success'] / total, 2)
            row['zalo_fail_ratio'] = round(100.0 * row['zalo_fail'] / total, 2)
            row['zalo_invalid_ratio'] = round(
                100.0 * row['zalo_invalid'] / total, 2)
            campaign.update(row)
