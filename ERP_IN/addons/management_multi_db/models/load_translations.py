# -*- encoding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import ValidationError, UserError
import datetime
import xmlrpclib
import socket
import requests


class LoadTranslations(models.Model):
    _name = 'load.translation'
    _description = 'Load Translations'
    _order = 'create_date desc'

    name = fields.Char()
    execute_date = fields.Datetime(default=datetime.datetime.now())
    db_ids = fields.Many2many('db.detail', 'load_translation_db_detail_rel',
                              'load_translation_id', 'db_id', required=True)
    state = fields.Selection([
        ('draft', 'New'),
        ('verified', 'Verified'),
        ('running', 'Running'),
        ('error', 'Error'),
        ('cancel', 'Cancelled'),
        ('done', 'Done')
    ], 'Status', copy=False, default="draft")
    db_language_log_ids = fields.One2many('db.language.log', 'load_translation_id')

    patch_upgrade = fields.Many2one('management.module', 'Patch upgrade', required=True)

    @api.multi
    def verify_all_db(self):
        for s in self:
            if s.db_ids:
                for db in s.db_ids:
                    db_language_log = s.env['db.language.log'].verify_db(db, s.id)
            s.write({'state': 'verified'})
        return True

    @api.multi
    def put_in_queue(self):
        for s in self:
            if s.db_language_log_ids:
                s.write({'state': 'running'})
                for db_language_log in s.db_language_log_ids:
                    if db_language_log.state == 'ready':
                        db_language_log.write({'state': 'in_queue'})
        return True

    @api.one
    def cancel(self):
        if self.db_language_log_ids:
            for db_language_log in self.db_language_log_ids:
                if db_language_log.state != 'done':
                    db_language_log.write({'state': 'cancel',
                                           'message': 'Cancelled load a language in the db'})
        self.write({'state': 'cancel'})

    @api.model
    def process_load_language(self):
        db_language_log_list = self.env['db.language.log'].search([('state', '=', 'in_queue')], limit=1)
        for db_language_log in db_language_log_list:
            db_language_log.write({'start_time': datetime.datetime.now()})
            try:
                try:
                    uid, sock = self.conect_db(db_language_log.db_id)
                except:
                    db_language_log.write({'state': 'error',
                                           'message': 'Load language fail',
                                           'end_time': datetime.datetime.now()})
                    db_language_log.try_change_state_db()
                    continue
                # check_vietnam_translate = db_language_log.check_install_vietnam_translate(db_language_log.db_id, uid, sock)
                # if not check_vietnam_translate:
                #     lang_install = db_language_log.lang_install(db_language_log.db_id, uid, sock)
                #     if not lang_install:
                #         db_language_log.write({'state': 'error',
                #                                'message': 'Load language fail',
                #                                'end_time': datetime.datetime.now()})
                #         db_language_log.try_change_state_db()
                #     db_language_log.write({'state': 'done',
                #                            'message': 'Load language success',
                #                            'end_time': datetime.datetime.now()})
                #     db_language_log.try_change_state_db()
                # lang_install = db_language_log.lang_install(db_language_log.db_id, uid, sock)
                # if not lang_install:
                #     db_language_log.write({'state': 'error',
                #                            'message': 'Load language fail',
                #                            'end_time': datetime.datetime.now()})
                #     db_language_log.try_change_state_db()
                vietname_translation = db_language_log.vietname_translation(db_language_log.db_id, uid, sock)
                if not vietname_translation:
                    db_language_log.write({'state': 'error',
                                           'message': 'Load a language success but vietnam translate fail',
                                           'end_time': datetime.datetime.now()})
                    db_language_log.try_change_state_db()
                db_language_log.write({'state': 'done',
                                       'message': 'Load language success',
                                       'end_time': datetime.datetime.now()})
                db_language_log.try_change_state_runtime_language()
            except:
                db_language_log.write({'state': 'error',
                                       'message': 'Load language fail',
                                       'end_time': datetime.datetime.now()})
                db_language_log.try_change_state_db()
                continue
        return True

    @api.multi
    def conect_db(self, db):
        sock_common = xmlrpclib.ServerProxy(
            "https://{}/xmlrpc/common".format(db.url))
        uid = sock_common.login(db.name, db.user_name, db.password)
        sock = xmlrpclib.ServerProxy("https://{}/xmlrpc/object".format(db.url))
        return uid, sock