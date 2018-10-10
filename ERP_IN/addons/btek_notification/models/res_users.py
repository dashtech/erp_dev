# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class ResUsersPlay(models.Model):
    _name = 'res.users.play'
    _description = 'ResUsersPlay'

    name = fields.Char('Play ID',
                       required=True)
    user_id = fields.Many2one(
        'res.users', 'User',
        required=True)

    _sql_constraints = [
        ('name_uniq',
         'unique(name, user_id)',
         _('Play ID must be unique per user !')),
    ]

class ResUsers(models.Model):
    _inherit = 'res.users'

    play_ids = fields.One2many(
        'res.users.play', 'user_id',
        'Play ID'
    )

    def set_playid(self, play_id):
        user_id = self._ids[0]
        domain = [('user_id', '=', user_id),
                  ('name', '=', play_id)]
        play_s = self.env['res.users.play'].search(domain)
        if play_s:
            return False

        self.env['res.users.play'].create(
            {
                'user_id': user_id,
                'name': play_id
            })

        return True

    def unset_playid(self, play_id):
        user_id = self._ids[0]
        domain = [('user_id', '=', user_id),
                  ('name', '=', play_id)]
        play_s = self.env['res.users.play'].search(domain)
        if not play_s:
            return False

        play_s.unlink()
        return True

    def get_playid(self):
        res = {}
        for user in self:
            res[str(user.id)] = [playid.name for playid in user.play_ids]
        return res

    def get_follow_dict(self, *args):
        user_id = self._ids and self._ids[0] or False
        user_condition = ''
        if user_id:
            user_condition = \
                ' and ru.id = {}'.format(user_id)

        # limit_str = self._ids and ' limit %d' % self._ids[1] or ''
        # offset_str = self._ids and ' offset %d' % self._ids[2] or ''
        # readed = self._ids[3] if self._ids[3] is not None else ''
        # sent = self._ids[4] if self._ids[4] is not None else ''

        limit_str = args[0] and ' limit %d' % args[0] or ''
        offset_str = args[1] and ' offset %d' % args[1] or ''
        readed = args[2] if args[2] is not None else ''
        sent = args[3] if args[3] is not None else ''
        if readed != '' and sent != '':
            querry = """
                        select mm.id as mm_id,
                          rp.name as partner_name,
                          ru.id as user_id,
                          ru.login as user_login
                        from mail_message as mm
                            left join mail_followers as mf
                            on mf.res_id = mm.res_id and mf.res_model = mm.model
                            left join res_users as ru
                            on ru.partner_id = mf.partner_id
                            left join res_partner as rp
                            on rp.id = ru.partner_id
                        where sent is {} and readed is {}
                          and message_type != 'email'
                          {} {} {}
                    """.format(sent, readed, user_condition, limit_str, offset_str)
        elif readed != '':
            querry = """
                        select mm.id as mm_id,
                          rp.name as partner_name,
                          ru.id as user_id,
                          ru.login as user_login
                        from mail_message as mm
                            left join mail_followers as mf
                            on mf.res_id = mm.res_id and mf.res_model = mm.model
                            left join res_users as ru
                            on ru.partner_id = mf.partner_id
                            left join res_partner as rp
                            on rp.id = ru.partner_id
                        where readed is {}
                          and message_type != 'email'
                          {} {} {}
                    """.format(readed, user_condition, limit_str, offset_str)
        elif sent != '':
            querry = """
                        select mm.id as mm_id,
                          rp.name as partner_name,
                          ru.id as user_id,
                          ru.login as user_login
                        from mail_message as mm
                            left join mail_followers as mf
                            on mf.res_id = mm.res_id and mf.res_model = mm.model
                            left join res_users as ru
                            on ru.partner_id = mf.partner_id
                            left join res_partner as rp
                            on rp.id = ru.partner_id
                        where sent is {} and message_type != 'email'
                          {} {} {}
                    """.format(sent, user_condition, limit_str, offset_str)
        else:
            querry = """
                    select mm.id as mm_id,
                      rp.name as partner_name,
                      ru.id as user_id,
                      ru.login as user_login
                    from mail_message as mm
                        left join mail_followers as mf
                        on mf.res_id = mm.res_id and mf.res_model = mm.model
                        left join res_users as ru
                        on ru.partner_id = mf.partner_id
                        left join res_partner as rp
                        on rp.id = ru.partner_id
                    where message_type != 'email'
                      {} {} {}
                """.format(user_condition, limit_str, offset_str)
        self.env.cr.execute(querry)

        message_ids = []
        follower_dict = {}
        for row in self.env.cr.dictfetchall():
            mm_id = row['mm_id']
            partner_name = row['partner_name']
            user_id = row['user_id']
            user_obj = self.env['res.users'].search([('id', '=', row['user_id'])])
            play_ids = {}
            if user_obj:
                play_ids[str(user_obj.id)] = [playid.name for playid in user_obj.play_ids]

            message_ids.append(mm_id)

            mm_id = str(mm_id)
            user_id = str(user_id)

            if not user_id or not partner_name:
                continue
            if not follower_dict.get(mm_id, False):
                follower_dict[mm_id] = {}

            follower_dict[mm_id][user_id] = partner_name, play_ids.values()

        return follower_dict, message_ids

    def get_unsent_message(self, limit=None, offset=0, read=None, sent=None):

        follower_dict, message_ids = self.get_follow_dict(limit, offset, read, sent)
        unsent_message_s = self.env['mail.message'].browse(message_ids)
        res = []
        for unsent_message in unsent_message_s:
            follower = follower_dict.get(
                str(unsent_message.id), False)
            if not follower:
                continue
            tracking = self.env['mail.message'
            ].get_tracking(unsent_message)
            res.append(
                {
                    'id': unsent_message.id,
                    'type': unsent_message.message_type,
                    'name': unsent_message.record_name,
                    'res_id': unsent_message.res_id,
                    'model': unsent_message.model,
                    'date': unsent_message.date,
                    'body': unsent_message.body,
                    'tracking': tracking,
                    'follower': follower,
                }
            )
        return res

    @api.multi
    def unsubscribe_notify(self, configuration_id=False):
        for user in self:
            blacklist = self.env['notify.blacklist'].search(
                [('user_id', '=', user.id),
                 ('configuration_id', '=', configuration_id)]
            )
            if blacklist:
                continue
            self.env['notify.blacklist'].create({
                'user_id': user.id,
                'configuration_id': configuration_id
            })
        return True

    @api.multi
    def get_info_to_notify_message(self):
        self.ensure_one()
        info = {
            'name': self.name
        }
        default_priority = \
            self.env[
                'priority.chanel.send.message.line'].get_chanel_selection()
        priority = [item[0] for item in default_priority]
        prioritys = \
            self.env['priority.chanel.send.message'].search(
                [('user_id', '=', self.id)])
        if prioritys:
            priority = [item.chanel for item in prioritys[0].line_ids]

        for chanel in priority:
            if chanel == 'app':
                if not self.play_ids:
                    continue
                address = self.play_ids.mapped('name')
                info['address'] = address
                info['channel'] = 'app'
                return info

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

    @api.one
    def set_priority_chanel_notify_message(self, chanel_list):
        if not chanel_list:
            return False

        line_ids = []
        sequence = 10
        for chanel in chanel_list:
            line_ids.append((0, 0, {
                'sequence': sequence,
                'chanel': chanel,
            }))
            sequence += 10

        prioritys = self.env['priority.chanel.send.message'].search(
            [('user_id', '=', self.id)]
        )

        priority = prioritys and prioritys[0] or False
        if not priority:
            priority = \
                self.env['priority.chanel.send.message'].create({
                    'user_id': self.id,
                    'line_ids': line_ids,
                })
            return True

        priority.write({
            'line_ids': [(5)]
        })
        priority.write({
            'line_ids': line_ids
        })
        return True
