# -*- coding: utf-8 -*-
from odoo import api, tools, fields, models, _

class ir_attachment(models.Model):
    _inherit = 'ir.attachment'

    def connect(self):
        return self.env['social.connect'].connect()

    @api.model
    def create(self, vals):

        res_model = vals.get('res_model', False)

        if res_model != 'album':
            return super(ir_attachment, self).create(vals)

        uid, password, db, sock = self.connect()
        id = sock.execute(db, uid, password,
                           self._name, 'create',
                           vals)
        res = self.browse(id)
        return res

    @api.multi
    def write(self, vals):
        if not self.env.context.get('in_social', False):
            return super(ir_attachment, self).write(vals)

        uid, password, db, sock = self.connect()

        res = sock.execute(db, uid, password,
                           self._name, 'write',
                           self._ids, vals)
        return res

    @api.multi
    def unlink(self):
        if not self.env.context.get('in_social', False):
            return super(ir_attachment, self).unlink()

        uid, password, db, sock = self.connect()
        res = sock.execute(db, uid, password,
                           self._name, 'unlink',
                           self._ids)
        return res

    @api.multi
    def name_get(self):
        if not self.env.context.get('in_social', False):
            return super(ir_attachment, self).name_get()

        uid, password, db, sock = self.connect()
        res = sock.execute(db, uid, password,
                           self._name, 'name_get',
                           self._ids)
        return res

    @api.model
    def name_search(
            self, name='', args=False,
            operator='ilike', limit=100):

        if not self.env.context.get('in_social', False):
            return super(ir_attachment, self).name_search(
                name, args, operator, limit)

        uid, password, db, sock = self.connect()
        res = sock.execute(db, uid, password,
                           self._name, 'name_search',
                           name, args, operator, limit)
        return res

    @api.model
    def search(self, args, offset=0,
               limit=False, order=False, count=False):

        if not self.env.context.get('in_social', False):
            return super(ir_attachment, self).search(
                args, offset, limit, order, count)

        uid, password, db, sock = self.connect()
        res = sock.execute(db, uid, password,
                           self._name, 'search',
                           args, offset, limit,
                           order, count)
        return res

    @api.multi
    def read(self, fields=False, load='_classic_read'):
        if not self.env.context.get('in_social', False):
            return super(ir_attachment, self).read(fields, load)

        uid, password, db, sock = self.connect()
        res = sock.execute(db, uid, password,
                           self._name, 'read',
                           self._ids, fields,
                           load)
        return res

    @api.model
    def search_read(self, domain=False, fields=False,
                    offset=0, limit=False, order=False):

        if not self.env.context.get('in_social', False):
            return super(ir_attachment, self).search_read(
                domain, fields, offset, limit, order)

        uid, password, db, sock = self.connect()

        model = self._name

        res = sock.execute(db, uid, password,
                           model, 'search_read',
                           domain, fields, offset,
                           limit, order)

        return res
