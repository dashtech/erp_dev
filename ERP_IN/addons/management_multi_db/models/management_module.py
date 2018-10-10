# -*- encoding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import ValidationError, UserError
import datetime
import xmlrpclib
import socket
import requests


class DBDetail(models.Model):
    _name = 'db.detail'
    _description = 'DB Detail'
    _order = 'priority desc'

    name = fields.Char(required=True)
    url = fields.Char(required=True)
    user_name = fields.Char(required=True)
    password = fields.Char(required=True)
    is_use = fields.Boolean(default=True)
    db_category = fields.Selection([('basic', 'Basic'),
                                    ('pro', 'Professional')], string='Db Category')
    priority = fields.Char('Priority')


class ModuleDetail(models.Model):
    _name = 'module.detail'
    _description = 'Module Detail'

    name = fields.Char(required=True)
    shortdesc = fields.Char()


class ManagementModule(models.Model):
    _name = 'management.module'
    _description = 'Management Module'
    _order = 'create_date desc'

    name = fields.Char()
    execute_date = fields.Datetime(default=datetime.datetime.now())
    action_type = fields.Selection([
        ('upgrade', 'Upgrade'),
        ('install', 'Install'),
        ], 'Action', default="upgrade", required=True)
    module_ids = fields.Many2many('module.detail', 'management_module_module_detail_rel', 'management_module_id', 'module_id', required=True)
    db_ids = fields.Many2many('db.detail', 'management_module_db_detail_rel', 'management_module_id', 'db_id', required=True)
    state = fields.Selection([
        ('draft', 'New'),
        ('verified', 'Verified'),
        ('running', 'Running'),
        ('error', 'Error'),
        ('cancel', 'Cancelled'),
        ('done', 'Done')
        ], 'Status', copy=False, default="draft")
    db_log_ids = fields.One2many('db.log', 'management_module_id')
    module_log_ids = fields.One2many('module.log', 'management_module_id')

    @api.multi
    def verify_all_db(self):
        for s in self:
            if s.db_ids:
                for db in s.db_ids:
                    db_log = s.env['db.log'].verify_db(db, s.id, s.module_ids)
            s.write({'state': 'verified'})
        return True

    @api.multi
    def put_in_queue(self):
        for s in self:
            if s.module_log_ids:
                s.write({'state': 'running'})
                for module_log in s.module_log_ids:
                    if module_log.state == 'ready':
                        module_log.write({'state': 'in_queue'})
        return True

    @api.one
    def cancel(self):
        if self.db_log_ids:
            for db_log in self.db_log_ids:
                if db_log.state != 'done':
                    db_log.write({'state': 'cancel'})
        if self.module_log_ids:
            for module_log in self.module_log_ids:
                if module_log.state != 'done':
                    module_log.write({'state': 'cancel'})
        self.write({'state': 'cancel'})

    @api.model
    def process_run_action(self):
        module_list = self.env['module.log'].search([('state', '=', 'in_queue')], limit=2)
        for module in module_list:
            module.write({'start_time': datetime.datetime.now()})
            try:
                try:
                    uid, sock = self.conect_db(module.db_id)
                except:
                    module.write({'state': 'error',
                                  'message': 'Module execute fail',
                                  'end_time': datetime.datetime.now()})
                    module.db_log_id.try_change_state_db()
                    module.db_log_id.try_change_state_runtime()
                    continue
                try:
                    module_in_db = sock.execute(
                        module.db_id.name, uid, module.db_id.password, 'ir.module.module',
                        'search_read', [('name', '=', module.module_detail_id.name)],
                        ['name'])
                except:
                    module.write({'state': 'error',
                                  'message': 'Module execute fail',
                                  'end_time': datetime.datetime.now()})
                    module.db_log_id.try_change_state_db()
                    module.db_log_id.try_change_state_runtime()
                    continue
                module_id_in_db = module_in_db[0]['id']
                runtime = module.run_excute(module.db_id, uid, sock, module, module_id_in_db)
                if not runtime:
                    module.write({'state': 'error',
                                  'message': 'Module execute fail',
                                  'end_time': datetime.datetime.now()})
                    module.db_log_id.try_change_state_db()
                    module.db_log_id.try_change_state_runtime()
                    continue
                module.write({'state': 'done',
                              'message': 'Module already executed successfully',
                              'end_time': datetime.datetime.now()})
                module.db_log_id.try_change_state_db()
                module.db_log_id.try_change_state_runtime()
            except:
                module.write({'state': 'error',
                              'message': 'Module execute fail',
                              'end_time': datetime.datetime.now()})
                module.db_log_id.try_change_state_db()
                module.db_log_id.try_change_state_runtime()
                continue
        return True

    @api.multi
    def conect_db(self, db):
        sock_common = xmlrpclib.ServerProxy(
            "https://{}/xmlrpc/common".format(db.url))
        uid = sock_common.login(db.name, db.user_name, db.password)
        sock = xmlrpclib.ServerProxy("https://{}/xmlrpc/object".format(db.url))
        return uid, sock
