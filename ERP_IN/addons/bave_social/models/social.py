# -*- coding: utf-8 -*-
from odoo import api, tools, fields, models, _
from odoo.exceptions import UserError
import xmlrpclib

class social_setting(models.Model):
    _name = 'social.setting'
    _description = 'social.setting'
    _rec_name = 'login'

    login = fields.Char()
    uid = fields.Integer(readonly=True)
    password = fields.Char()
    url = fields.Char()
    db = fields.Char()

    def get_info(self):
        record = self.env.ref('bave_social.social_setting_unique')
        return record

class social_connect(models.Model):
    _name = 'social.connect'

    def connect(self):
        setting = self.env['social.setting'].get_info()

        url = setting.url
        db = setting.db
        login = setting.login
        password = setting.password

        sock_common = xmlrpclib.ServerProxy(
            "{}/xmlrpc/common".format(url))

        # try:
        uid = sock_common.login(db, login, password)
        # except:
        #     raise UserError('Error: cannot connect to Bave social!')

        sock = xmlrpclib.ServerProxy(
            "{}/xmlrpc/object".format(url))

        return uid, password, db, sock

    # @api.model
    # def fields_view_get(self, view_id=False, view_type='form',
    #                     toolbar=False, submenu=False):
    #     uid, password, db, sock = self.connect()
    #
    #     res = sock.execute(db, uid, password,
    #                        self._name, 'fields_view_get',
    #                        view_id, view_type, toolbar, submenu)
    #     return res
    #
    # @api.model
    # def fields_get(self, allfields=False, attributes=False):
    #     uid, password, db, sock = self.connect()
    #
    #     res = sock.execute(db, uid, password,
    #                        self._name, 'fields_view_get',
    #                        allfields, attributes)
    #     return res

    @api.model
    def create(self, vals):
        uid, password, db, sock = self.connect()
        id = sock.execute(db, uid, password,
                           self._name, 'create',
                           vals)
        res = self.env[self._name].browse(id)
        return res

    @api.multi
    def write(self, vals):
        uid, password, db, sock = self.connect()

        res = sock.execute(db, uid, password,
                           self._name, 'write',
                           self._ids, vals)
        return res

    @api.multi
    def unlink(self):
        uid, password, db, sock = self.connect()
        res = sock.execute(db, uid, password,
                           self._name, 'unlink',
                           self._ids)
        return res

    @api.multi
    def copy_data(self, default=False):
        uid, password, db, sock = self.connect()
        res = sock.execute(db, uid, password,
                           self._name, 'copy_data',
                           self._ids, default)
        return res

    @api.multi
    def copy(self, default=False):
        uid, password, db, sock = self.connect()
        res = sock.execute(db, uid, password,
                           self._name, 'copy',
                           self._ids, default)
        return res

    @api.multi
    def name_get(self):
        uid, password, db, sock = self.connect()
        res = sock.execute(db, uid, password,
                           self._name, 'name_get',
                           self._ids)
        return res

    @api.model
    def name_search(
            self, name='', args=False,
            operator='ilike', limit=100):
        uid, password, db, sock = self.connect()
        res = sock.execute(db, uid, password,
                           self._name, 'name_search',
                           name, args, operator, limit)
        return res

    @api.model
    def search(self, args, offset=0,
               limit=False, order=False, count=False):
        uid, password, db, sock = self.connect()
        res = sock.execute(db, uid, password,
                           self._name, 'search',
                           args, offset, limit,
                           order, count)
        return res

    @api.multi
    def read(self, fields=False, load='_classic_read'):
        uid, password, db, sock = self.connect()
        res = sock.execute(db, uid, password,
                           self._name, 'read',
                           self._ids, fields,
                           load)
        return res

    @api.model
    def search_read(self, domain=False, fields=False,
                    offset=0, limit=False, order=False):
        uid, password, db, sock = self.connect()

        model = self._name

        res = sock.execute(db, uid, password,
                           model, 'search_read',
                           domain, fields, offset,
                           limit, order)

        return res

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=False,
                   orderby=False, lazy=True):
        uid, password, db, sock = self.connect()

        model = self._name

        res = sock.execute(db, uid, password,
                           model, 'read_group',
                           domain, fields, groupby,
                           offset, limit, orderby, lazy)
        return res

    @api.model
    def default_get(self, fields):
        uid, password, db, sock = self.connect()

        model = self._name
        res = sock.execute(db, uid, password,
                           model, 'default_get',
                           fields)
        return res

