# -*- coding: utf-8 -*-
import odoo
from odoo import http, SUPERUSER_ID
from odoo.http import request, content_disposition
from odoo.tools.translate import _
import functools
from odoo.modules import get_resource_path
from cStringIO import StringIO
import imghdr
import base64

db_list = http.db_list

db_monodb = http.db_monodb


DEFAULT_DATE_FORMAT = '%m/%d/%Y'


class BtekViewImage(http.Controller):

    @http.route(['/product_template/image_medium/<int:product_id>'], type='http', auth="none", cors="*")
    def product_image_nodb(self, dbname=None, **kw):
        imgname = 'nologo'
        imgext = '.png'

        product_id = kw['product_id']
        placeholder = functools.partial(get_resource_path, 'web', 'static', 'src', 'img')
        uid = None
        if request.session.db:
            dbname = request.session.db
            uid = request.session.uid
        elif dbname is None:
            dbname = db_monodb()

        if not uid:
            uid = SUPERUSER_ID

        if not dbname or not product_id:
            response = http.send_file(placeholder(imgname + imgext))
        else:
            imgname = 'product_' + str(product_id)
            try:
                # create an empty registry
                product = request.env['product.template'].sudo().browse(product_id)
                if product:
                    image_base64 = str(product.image_small).decode('base64')
                    image_data = StringIO(image_base64)
                    imgext = '.' + (imghdr.what(None, h=image_base64) or 'png')
                    response = http.send_file(image_data, filename=imgname + imgext)
                else:
                    response = http.send_file(placeholder('nologo.png'))
            except Exception:
                response = http.send_file(placeholder(imgname + imgext))

        return response

    @http.route(['/fleet_vehicle/image_medium/<int:fleet_id>'], type='http', auth="none", cors="*")
    def vehicle_image_nodb(self, dbname=None, **kw):
        imgname = 'nologo'
        imgext = '.png'

        fleet_id = kw['fleet_id']
        placeholder = functools.partial(get_resource_path, 'web', 'static', 'src', 'img')
        uid = None
        if request.session.db:
            dbname = request.session.db
            uid = request.session.uid
        elif dbname is None:
            dbname = db_monodb()

        if not uid:
            uid = SUPERUSER_ID

        if not dbname or not fleet_id:
            response = http.send_file(placeholder(imgname + imgext))
        else:
            imgname = 'vehicle_' + str(fleet_id)
            try:
                # create an empty registry
                vehicle = request.env['fleet.vehicle'].sudo().browse(fleet_id)
                if vehicle:
                    image_base64 = str(vehicle.image_small).decode('base64')
                    image_data = StringIO(image_base64)
                    imgext = '.' + (imghdr.what(None, h=image_base64) or 'png')
                    response = http.send_file(image_data, filename=imgname + imgext)
                else:
                    response = http.send_file(placeholder('nologo.png'))
            except Exception:
                response = http.send_file(placeholder(imgname + imgext))

        return response

    @http.route(['/res_partner/image/<int:partner_id>'], type='http', auth="none", cors="*")
    def res_partner_image_nodb(self, dbname=None, **kw):
        imgname = 'nologo'
        imgext = '.png'

        partner_id = kw['partner_id']
        placeholder = functools.partial(get_resource_path, 'web', 'static', 'src', 'img')
        uid = None
        if request.session.db:
            dbname = request.session.db
            uid = request.session.uid
        elif dbname is None:
            dbname = db_monodb()

        if not uid:
            uid = SUPERUSER_ID

        if not dbname or not partner_id:
            response = http.send_file(placeholder(imgname + imgext))
        else:
            imgname = 'partner_' + str(partner_id)
            try:
                # create an empty registry
                partner = request.env['res.partner'].sudo().browse(partner_id)
                if partner:
                    image_base64 = str(partner.image_small).decode('base64')
                    image_data = StringIO(image_base64)
                    imgext = '.' + (imghdr.what(None, h=image_base64) or 'png')
                    response = http.send_file(image_data, filename=imgname + imgext)
                else:
                    response = http.send_file(placeholder('nologo.png'))
            except Exception:
                response = http.send_file(placeholder(imgname + imgext))

        return response

    @http.route(['/fleet_repair/car_image/<int:repair_id>'], type='http', auth="none", cors="*")
    def fleet_repair_image_nodb(self, dbname=None, **kw):
        imgname = 'nologo'
        imgext = '.png'

        repair_id = kw['repair_id']
        placeholder = functools.partial(get_resource_path, 'web', 'static', 'src', 'img')
        uid = None
        if request.session.db:
            dbname = request.session.db
            uid = request.session.uid
        elif dbname is None:
            dbname = db_monodb()

        if not uid:
            uid = SUPERUSER_ID

        if not dbname or not repair_id:
            response = http.send_file(placeholder(imgname + imgext))
        else:
            imgname = 'repair_' + str(repair_id)
            try:
                # create an empty registry
                repair = request.env['fleet.repair'].sudo().browse(repair_id)
                if repair:
                    image_base64 = str(repair.car_image).decode('base64')
                    image_data = StringIO(image_base64)
                    imgext = '.' + (imghdr.what(None, h=image_base64) or 'png')
                    response = http.send_file(image_data, filename=imgname + imgext)
                else:
                    response = http.send_file(placeholder('nologo.png'))
            except Exception:
                response = http.send_file(placeholder(imgname + imgext))

        return response

