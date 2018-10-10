# -*- coding: utf-8 -*-
from odoo import api, tools, fields, models, _


class MultiImages(models.Model):
    _name = "images"

    image = fields.Binary('Images')
    description = fields.Char('Description')
    title = fields.Char('title')
    album_id = fields.Many2one('album', 'Album')


class Album(models.Model):
    _name = 'album'
    _description = 'Album'

    name = fields.Char(required=True)
    title = fields.Char()
    description = fields.Char()
    view_count = fields.Float()
    like_count = fields.Float()
    provider_id = fields.Many2one(
        'service.provider', 'Provider')
    active = fields.Boolean(default=True)

    attachment_ids = fields.Many2many(
        'ir.attachment', 'album_attachment_rel',
        'album_id', 'attachment_id', 'Attachments'
    )
    images = fields.One2many(
        'images', 'album_id',
        'Multi Images')


