# -*- encoding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import ValidationError, UserError
import xmlrpclib
import socket
import requests
import datetime
import json


class DBLog(models.Model):
    _name = 'module.log'
    _description = 'Module Log'
    _order = 'db_log_id,sequence,id'

    name = fields.Char()
    sequence = fields.Integer()
    management_module_id = fields.Many2one('management.module')
    db_id = fields.Many2one('db.detail')
    db_log_id = fields.Many2one('db.log')
    module_detail_id = fields.Many2one('module.detail')
    state = fields.Selection([
        ('draft', 'New'),
        ('ready', 'Ready'),
        ('in_queue', 'In Queue'),
        ('error', 'Error'),
        ('cancel', 'Cancelled'),
        ('done', 'Done')
    ], 'Status', copy=False, default="draft")
    message = fields.Text()
    start_time = fields.Datetime()
    end_time = fields.Datetime()
    delta_time = fields.Float(compute='_compute_delta_time', store=True)

    @api.depends('start_time', 'end_time')
    @api.multi
    def _compute_delta_time(self):
        for s in self:
            if s.start_time:
                start_time = datetime.datetime.strptime(s.start_time, '%Y-%m-%d %H:%M:%S')
            else:
                continue
            if s.end_time:
                end_time = datetime.datetime.strptime(s.end_time, '%Y-%m-%d %H:%M:%S')
            else:
                continue
            delta_time = end_time - start_time
            s.delta_time = delta_time.seconds

    def verify_all_module(self, module_ids, module_dict, db, db_log_id):
        sequence = 0
        for module in module_ids:
            sequence += 1
            self.verify_module(module, module_dict, db, db_log_id, sequence)
        return True

    def verify_module(self, module, module_dict, db, db_log_id, sequence):
        module_log = self.create({
            'name': 'Check {}'.format(module.name),
            'sequence': sequence,
            'management_module_id': db_log_id.management_module_id.id,
            'db_log_id': db_log_id.id,
            'db_id': db.id,
            'module_detail_id': module.id,
            'state': 'draft'
        })
        state = module_dict.get(module.name)['state']
        if module_log.management_module_id.action_type == 'upgrade':
            if state == 'uninstalled':
                module_log.write({
                    'state': 'error',
                    'message': 'module {} is not installed in {}'.format(module.name, db.name)})
            elif state != 'installed':
                module_log.write({
                    'state': 'error',
                    'message': 'module {} is not ready to upgrade'.format(module.name)})
            else:
                module_log.write({
                    'state': 'ready',
                    'message': 'module {} is ready to upgrade'.format(module.name)})
        else:
            if state == 'installed':
                module_log.write({
                    'state': 'error',
                    'message': 'module {} is installed in {}'.format(module.name, db.name)})
            elif state != 'uninstalled':
                module_log.write({
                    'state': 'error',
                    'message': 'module {} is not ready to install'.format(module.name)})
            else:
                module_log.write({
                    'state': 'ready',
                    'message': 'module {} is ready to install'.format(module.name)})
        db_log_id.try_change_state_db()
        return module_log

    def run_excute(self, db, uid, sock, module, module_id_in_db):
        if module.management_module_id.action_type == 'upgrade':
            return self.update_module(db, uid, sock, module_id_in_db)
        return self.install_module(db, uid, sock, module_id_in_db)

    def update_module(self, db, uid, sock, module_id_in_db):
        if not self.db_log_id.is_install_upgrade_module_from_http:
            try:
                update = sock.execute(db.name, uid, db.password,
                             'ir.module.module', 'button_immediate_upgrade', [module_id_in_db])
            except:
                return False
        else:
            url = 'https://' + db.url + '/upgrade_module/{}/{}'.format(self.module_detail_id.name, db.user_name)
            data = {"password": db.password}
            headers = {'key': 'value'}
            response = requests.post(url, data, headers=headers)
            response_text = response.text
            res = json.loads(response_text)
            if res['result'] is not True:
                return False
        return True

    def install_module(self, db, uid, sock, module_id_in_db):
        try:
            install = sock.execute(db.name, uid, db.password,
                         'ir.module.module', 'button_immediate_install', [module_id_in_db])
        except:
            return False
        return True


class DBLog(models.Model):
    _name = 'db.log'
    _description = 'DB Log'

    name = fields.Char()
    management_module_id = fields.Many2one('management.module')
    db_id = fields.Many2one('db.detail')
    state = fields.Selection([
        ('draft', 'New'),
        ('ready', 'Ready'),
        ('error', 'Error'),
        ('cancel', 'Cancelled'),
        ('done', 'Done')
    ], 'Status', copy=False, default="draft")
    message = fields.Text()
    module_log_ids = fields.One2many('module.log', 'db_log_id')
    parent_state = fields.Selection([
        ('draft', 'New'),
        ('verified', 'Verified'),
        ('running', 'Running'),
        ('error', 'Error'),
        ('cancel', 'Cancelled'),
        ('done', 'Done')
        ], related='management_module_id.state', readonly=True, store=True)
    is_install_upgrade_module_from_http = fields.Boolean(default=False, readonly=True)

    def verify_db(self, db, management_module_id, module_ids):
        db_log = self.create({
            'name': 'Check {}'.format(db.name),
            'management_module_id': management_module_id,
            'is_install_upgrade_module_from_http': False,
            'db_id': db.id,
            'state': 'draft'
        })

        try:
            check_url = self.check_url(db.url)
        except:
            db_log.write({
                'state': 'error',
                'message': 'URL invalid'})
            return db_log
        if not check_url:
            db_log.write({
                'state': 'error',
                'message': 'cannot connect to {}'.format(db.name)})
            return db_log
        try:
            uid, sock, module_dict = self.conect_db(db, module_ids)
        except:
            db_log.write({
                'state': 'error',
                'message': 'cannot connect to {}'.format(db.name)})
            return db_log
        if not uid:
            db_log.write({
                'state': 'error',
                'message': 'user or passwor of {} is invalid'.format(
                    db.name)})
            return db_log
        try:
            update_app_list = self.update_app_list(db, uid, sock)
            db_log.write({
                'state': 'ready',
                'message': '{} update app list success'.format(
                    db.name)})
        except:
            db_log.write({
                'state': 'error',
                'message': 'cannot update applist in {}'.format(db.name)})
            return db_log
        upgrade_module_from_http = self.check_install_upgrade_module_from_http(module_dict)
        if upgrade_module_from_http:
            db_log.write({
                'is_install_upgrade_module_from_http': True})
        if db_log.state == 'ready':
            module_log = self.env['module.log'].verify_all_module(module_ids, module_dict, db, db_log)
        return db_log

    def re_verify_db(self):
        module_log_exists_in_db_log = self.env['module.log'].search([('db_log_id', '=', self.id)])

        module_log_exists_in_db_log.unlink()

        try:
            check_url = self.check_url(self.db_id.url)
        except:
            self.write({
                'state': 'error',
                'message': 'URL invalid'})
            return
        if not check_url:
            self.write({
                'state': 'error',
                'message': 'cannot connect to {}'.format(self.db_id.name)})
            return
        try:
            uid, sock, module_dict = self.conect_db(self.db_id, self.management_module_id.module_ids)
        except:
            self.write({
                'state': 'error',
                'message': 'cannot connect to {}'.format(self.db_id.name)})
            return
        if not uid:
            self.write({
                'state': 'error',
                'message': 'user or passwor of {} is invalid'.format(
                    self.db_id.name)})
            return
        try:
            update_app_list = self.update_app_list(self.db_id, uid, sock)
            self.write({
                'state': 'ready',
                'message': '{} update app list success'.format(
                    self.db_id.name)})
        except:
            self.write({
                'state': 'error',
                'message': 'cannot update applist in {}'.format(self.db_id.name)})
            return
        if self.state == 'ready':
            module_log = self.env['module.log'].verify_all_module(self.management_module_id.module_ids,
                                                                  module_dict,
                                                                  self.db_id, self)
        return True

    def check_url(self, url):
        r = requests.get("https://{}".format(url))
        if r.status_code == 200:
            return True
        return False

    @api.multi
    def conect_db(self, db, module_ids):
        sock_common = xmlrpclib.ServerProxy("https://{}/xmlrpc/common".format(db.url))
        uid = sock_common.login(db.name, db.user_name, db.password)
        sock = xmlrpclib.ServerProxy("https://{}/xmlrpc/object".format(db.url))
        module_name_list = []
        for module_id in module_ids:
            module_name_list.append(str(module_id.name or ''))
        module_name_list.append('upgrade_module_from_http')
        module_state_list = sock.execute(
            db.name, uid, db.password, 'ir.module.module',
            'search_read', [('name', 'in', module_name_list)], ['name', 'state'])

        module_dict = dict(
            (module_s['name'], module_s) for module_s in module_state_list)
        return uid, sock, module_dict

    @api.multi
    def update_app_list(self, db, uid, sock):
        vals = {}
        bmu_id = sock.execute(db.name, uid, db.password,
                              'base.module.update', 'create', vals)
        sock.execute(db.name, uid, db.password,
                     'base.module.update', 'update_module', [bmu_id])
        return True

    def try_change_state_db(self):
        module_log_error_s = self.env['module.log'].search([('db_log_id', '=', self.id), ('state', '=', 'error')])
        if module_log_error_s:
            self.write({'state': 'error'})
            return
        module_log_not_done_s = self.env['module.log'].search([('db_log_id', '=', self.id), ('state', '!=', 'done')])
        if module_log_not_done_s:
            return
        self.write({'state': 'done'})
        self.write({'message': 'All module in the db are execute successful'})
        return

    def try_change_state_runtime(self):
        db_log_error_s = self.search([('management_module_id', '=', self.management_module_id.id), ('state', '=', 'error')])
        if db_log_error_s:
            self.management_module_id.write({'state': 'error'})
            return
        db_log_not_done_s = self.env['module.log'].search([('management_module_id', '=', self.management_module_id.id), ('state', '!=', 'done')])
        if db_log_not_done_s:
            return
        self.management_module_id.write({'state': 'done'})
        return

    def check_install_upgrade_module_from_http(self, module_dict):
        temp = module_dict.get('upgrade_module_from_http' or False)
        if temp:
            if temp['state'] == 'installed':
                return True
        return False


class DBLog(models.Model):
    _name = 'db.language.log'
    _description = 'DB Language Log'

    name = fields.Char()
    load_translation_id = fields.Many2one('load.translation')
    db_id = fields.Many2one('db.detail')
    state = fields.Selection([
        ('draft', 'New'),
        ('ready', 'Ready'),
        ('in_queue', 'In Queue'),
        ('error', 'Error'),
        ('cancel', 'Cancelled'),
        ('done', 'Done')
    ], 'Status', copy=False, default="draft")
    message = fields.Text()
    start_time = fields.Datetime()
    end_time = fields.Datetime()
    delta_time = fields.Float(compute='_compute_delta_time', store=True)
    parent_state = fields.Selection([
        ('draft', 'New'),
        ('verified', 'Verified'),
        ('running', 'Running'),
        ('error', 'Error'),
        ('cancel', 'Cancelled'),
        ('done', 'Done')
    ], related='load_translation_id.state', readonly=True, store=True)

    @api.depends('start_time', 'end_time')
    @api.multi
    def _compute_delta_time(self):
        for s in self:
            if s.start_time:
                start_time = datetime.datetime.strptime(s.start_time,
                                                        '%Y-%m-%d %H:%M:%S')
            else:
                continue
            if s.end_time:
                end_time = datetime.datetime.strptime(s.end_time,
                                                      '%Y-%m-%d %H:%M:%S')
            else:
                continue
            delta_time = end_time - start_time
            s.delta_time = delta_time.seconds

    def verify_db(self, db, load_translation_id):
        db_language_log = self.create({
            'name': 'Check {}'.format(db.name),
            'load_translation_id': load_translation_id,
            'db_id': db.id,
            'state': 'draft'
        })

        try:
            check_url = self.env['db.log'].check_url(db.url)
        except:
            db_language_log.write({
                'state': 'error',
                'message': 'URL invalid'})
            return db_language_log
        if not check_url:
            db_language_log.write({
                'state': 'error',
                'message': 'cannot connect to {}'.format(db.name)})
            return db_language_log
        try:
            uid, sock = self.env['management.module'].conect_db(db)
        except:
            db_language_log.write({
                'state': 'error',
                'message': 'cannot connect to {}'.format(db.name)})
            return db_language_log
        if not uid:
            db_language_log.write({
                'state': 'error',
                'message': 'user or passwor of {} is invalid'.format(
                    db.name)})
            return db_language_log
        db_language_log.write({
            'state': 'ready',
            'message': '{} is ready to load a translation.'.format(db.name)})
        return db_language_log

    @api.multi
    def re_verify_db(self):
        for s in self:
            try:
                check_url = s.env['db.log'].check_url(s.db_id.url)
            except:
                s.write({
                    'state': 'error',
                    'message': 'URL invalid'})
                return True
            if not check_url:
                s.write({
                    'state': 'error',
                    'message': 'cannot connect to {}'.format(s.db_id.name)})
                return True
            try:
                uid, sock = s.env['management.module'].conect_db(s.db_id)
            except:
                s.write({
                    'state': 'error',
                    'message': 'cannot connect to {}'.format(s.db_id.name)})
                return True
            if not uid:
                s.write({
                    'state': 'error',
                    'message': 'user or passwor of {} is invalid'.format(
                        s.db_id.name)})
                return True
            s.write({
            'state': 'ready',
            'message': '{} is ready to load a translation.'.format(s.db_id.name)})
        return True

    @api.multi
    def lang_install(self, db, uid, sock):
        vals = {'lang': 'vi_VN', 'overwrite': True}
        try:
            lad_id = sock.execute(db.name, uid, db.password,
                                  'base.language.install', 'create', vals)
        except:
            return False
        try:
            sock.execute(db.name, uid, db.password,
                         'base.language.install', 'lang_install', [lad_id])
        except:
            return False
        return True

    @api.multi
    def vietname_translation(self, db, uid, sock):
        vals = {}
        module_dict = {}
        module_arr = []
        modules_patch = self.load_translation_id.patch_upgrade.module_ids
        for module_id in modules_patch:
            module_name = sock.execute(db.name, uid, db.password, 'ir.module.module', 'search_read',
                                       [('name', '=', module_id.name),
                                        ('state', '=', 'installed')], ['id'])
            module_arr.append(module_name[0]['id'])
        module_dict.update({
            'module_upgrade': [(6, 0, module_arr)]
        })
        try:
            vitr_id = sock.execute(db.name, uid, db.password,
                                  'base.language.update', 'create', vals)
            sock.execute(db.name, uid, db.password,
                         'base.language.update', 'write', vitr_id, module_dict)
        except:
            return False
        try:
            sock.execute(db.name, uid, db.password,
                         'base.language.update', 'update_language', [vitr_id])
        except:
            return False
        return True

    def check_install_vietnam_translate(self, db, uid, sock):
        try:
            vietnam_translate_in_db = sock.execute(
                db.name, uid, db.password, 'ir.module.module', 'search_read',
                [('name', '=', 'vietnam_translate')], ['name', 'state'])
        except:
            return False
        if not vietnam_translate_in_db:
            return False
        if vietnam_translate_in_db[0]['state'] != 'installed':
            return False
        return True

    def try_change_state_runtime_language(self):
        db_log_error_s = self.search([('load_translation_id', '=', self.load_translation_id.id), ('state', '=', 'error')])
        if db_log_error_s:
            self.load_translation_id.write({'state': 'error'})
            return
        db_log_not_done_s = self.search([('load_translation_id', '=', self.load_translation_id.id), ('state', '!=', 'done')])
        if db_log_not_done_s:
            return
        self.load_translation_id.write({'state': 'done'})
        return

