# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from copy import deepcopy
from datetime import date, time, datetime

class CarColor(models.Model):
    _name = 'fleet.vehicle.color'
    _description = 'Vehicle Color'

    name = fields.Char(required=True)
    color_code = fields.Char()
    description = fields.Char()
    active = fields.Boolean(default=True)
    car_vehicle_model_ids = fields.Many2many(
        'fleet.vehicle.model', 'fleet_vehicle_model_color_rel',
        'color_id', 'model_id',
        string='Models')


class FleetVehicleModel(models.Model):
    _inherit = "fleet.vehicle.model"

    vehicle_version_id = fields.Many2one('fleet.vehicle.version',
                                         string='Vehicle Version')
    product_ids = fields.Many2many("product.template",
                                   "vehicle_model_id",
                                   string="Product")
    car_color_ids = fields.Many2many(
        'fleet.vehicle.color', 'fleet_vehicle_model_color_rel',
        'model_id', 'color_id',
        string='Colors')

    @api.multi
    @api.depends('name', 'brand_id', 'vehicle_version_id')
    def name_get(self):
        res = []
        for record in self:
            name = record.name
            version = \
                record.vehicle_version_id and \
                u'/{}'.format(record.vehicle_version_id.name) or ''
            if record.brand_id.name:
                name = record.brand_id.name + '/' + name + version
            res.append((record.id, name))
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if self.env.context.get('from_vehicle', False):
            for k, _domain in enumerate(args):
                if _domain[0] == "brand_id" and _domain[2]:
                    args[k] = ['brand_id', 'in', _domain[2][0][2]]
        return super(FleetVehicleModel, self).name_search(name, args=args, operator=operator, limit=limit)

    @api.multi
    def write(self, value):
        old_product_ids = self.product_ids
        res = super(FleetVehicleModel, self).write(value)
        if res and "product_ids" in value and self.env.context.get('FROM_FLEET', True):
            for product in self.product_ids:
                if product not in old_product_ids:
                    vehicle_model_id = product.vehicle_model_id.ids
                    vehicle_model_id.extend(self.ids)
                    brand = product.fleet_vehicle_brand_id.ids
                    brand.extend(self.ids)
                    value_write = {'vehicle_model_id': [[6, False, vehicle_model_id]],
                                   'fleet_vehicle_brand_id': [[6, False, brand]]}
                    product.with_context(FROM_FLEET=False).write(value_write)
            product_destroy = [x for x in old_product_ids if x not in self.product_ids]
            for pro_des in product_destroy:
                vehicle_model_id = pro_des.vehicle_model_id.ids
                for _id in self.ids:
                    if _id in vehicle_model_id:
                        vehicle_model_id.remove(_id)
                value_write = {'vehicle_model_id': [[6, False, vehicle_model_id]]}
                pro_des.with_context(FROM_FLEET=False).write(value_write)
        return res

    @api.model
    def create(self, value):
        res = super(FleetVehicleModel, self).create(value)
        if res:
            for product in res.product_ids:
                vehicle_model_id = product.vehicle_model_id.ids
                vehicle_model_id.extend(res.ids)
                brand = product.fleet_vehicle_brand_id.ids
                brand.extend(res.ids)
                value_write = {'vehicle_model_id': [[6, False, vehicle_model_id]],
                               'fleet_vehicle_brand_id': [[6, False, brand]]}
                product.with_context(FROM_FLEET=False).write(value_write)
        return res

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if self.env.context.get('from_vehicle', False):
            for k, _domain in enumerate(domain):
                if _domain[0] == "brand_id" and _domain[2]:
                    domain[k] = ['brand_id', 'in', _domain[2][0][2]]
        return super(FleetVehicleModel, self).search_read(domain=domain, fields=fields,
                                                          offset=offset, limit=limit, order=order)


FleetVehicleModel()


class FleetVehicleBrand(models.Model):

    _inherit = "fleet.vehicle.model.brand"

    product_id = fields.Many2many("product.template", "fleet_vehicle_brand_id", string="Product")


FleetVehicleModel()

class FleetVehicleType(models.Model):
    _name = 'fleet.vehicle.type'
    _description = 'Fleet vehicle type'

    name = fields.Char(required=True)
    description = fields.Char()
    active = fields.Boolean(default=True)


class FleetFleet(models.Model):
    _inherit = 'fleet.vehicle'
    _rec_name = 'car_info'

    brand_id = fields.Many2one('fleet.vehicle.model.brand',
                               'Brand', required=True, readonly=False,
                               related='model_id.brand_id',
                               help='Model of the vehicle')
    model_id = fields.Many2one('fleet.vehicle.model', 'Model',
                               required=True, help='Model of the vehicle')
    service_count = fields.Integer(compute="_compute_count_repair",
                                   string='Services')
    driver_id = fields.Many2one('res.partner', string='Car Owner',
                                help='Driver of the vehicle')
    type_id = fields.Many2one('fleet.vehicle.type', 'Type')
    color_id = fields.Many2one('fleet.vehicle.color', 'Color')
    # license_plate = fields.Char(required=False, default=_default_get,
    #                             help='License plate number of the vehicle (i = plate number for a car)')

    car_info = fields.Char('Car Information',
                           compute='_cus_compute_vehicle_name', store=True)
    gas_number = fields.Float('Gas number')
    car_color_id = fields.Many2one('car.color', string="Color")

    name = fields.Char('')

    vin_sn = fields.Char('VIN Number', help='Unique number written on the vehicle motor (VIN/SN number)',
                         copy=False)
    chassis_number = fields.Char('Chassis Number',
                                 copy=False)

    _sql_constraints = [
        ('license_plate_uniq', 'unique(license_plate)', 'The license plate is already in your system. Please check your system again!'),
    ]

    @api.multi
    @api.depends('model_id.brand_id.name', 'model_id.vehicle_version_id.name', 'license_plate')
    def _cus_compute_vehicle_name(self):
        for vehicle in self:
            brand_name = vehicle.model_id.brand_id.name or ''
            license_plate = vehicle.license_plate or ''
            model_name = vehicle.model_id.name or ''
            version_name = vehicle.model_id.vehicle_version_id.name or ''
            car_info = [brand_name, model_name]
            if version_name:
                car_info.append(version_name)
            car_info.append(license_plate)
            vehicle.car_info = \
                '/'.join(car_info)

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        priority_partner_id = self.env.context.get('priority_partner_id', False)

        if not priority_partner_id:
            return super(FleetFleet, self).name_search(name, args=args, operator=operator, limit=limit)

        orders = self.env['sale.order'].search(
            [('partner_id', '=', priority_partner_id),
             ('create_form_fleet', '=', True),
             ('state', '!=', 'cancel')]
        )
        if not orders:
            return super(FleetFleet, self).name_search(name, args=args, operator=operator, limit=limit)
        fleet_ids = orders.mapped('fleet_ids')

        if not fleet_ids:
            return super(FleetFleet, self).name_search(name, args=args, operator=operator, limit=limit)

        args = args or []
        priority_args = deepcopy(args)
        priority_args.append(('id', 'in', fleet_ids._ids))

        priority_res = super(FleetFleet, self).name_search(
            name, args=priority_args, operator=operator, limit=limit)
        limit = limit or 100
        priority_fleet_ids = [f[0] for f in priority_res]

        deficient_qty = limit - len(priority_res)

        if deficient_qty <= 0:
            return priority_res

        args.append(('id', 'not in', priority_fleet_ids))
        deficient_res = super(FleetFleet, self).name_search(
            name, args=args, operator=operator, limit=deficient_qty)

        priority_res.extend(deficient_res)

        return priority_res

    @api.model
    def create(self, vals):
        res = super(FleetFleet, self).create(vals)
        # car_info = res.model_id.brand_id.name + '_Serial_' + res.license_plate
        # res['car_info'] = car_info
        return res

    @api.multi
    def write(self, values):
        # if values.get('model_id') or values.get('license_plate'):
        #     vehicle_model = self.env['fleet.vehicle.model'].search([('id', '=', values.get('model_id'))])
        #     car_info = str(vehicle_model.brand_id.name if vehicle_model else self.model_id.brand_id.name) \
        #                + '_Serial_' + \
        #                str(values.get('license_plate') if values.get('license_plate') else self.license_plate)
        #     values['car_info'] = car_info
        return super(FleetFleet, self).write(values)

    # license_plate = fields.Char(required=True, default=auto_fill_license_plate,
    #                             help='License plate number of the vehicle (i = plate number for a car)')
    # product_ids = fields.Many2many("product.template", "fleet_vehicle_id", string="Product ")

    # @api.multi
    # def write(self, value):
    #     old_product_ids = self.product_ids
    #     res = super(FleetFleet, self).write(value)
    #     if res and "product_ids" in value and self.env.context.get('FROM_FLEET', True):
    #         for product in self.product_ids:
    #             if product not in old_product_ids:
    #                 fleet_vehicle_id = product.fleet_vehicle_id.ids
    #                 fleet_vehicle_id.extend(self.ids)
    #                 value_write = {'fleet_vehicle_id': [[6, False, fleet_vehicle_id]]}
    #                 product.with_context(FROM_FLEET=False).write(value_write)
    #         product_destroy = [x for x in old_product_ids if x not in self.product_ids]
    #         for pro_des in product_destroy:
    #             fleet_vehicle_id = pro_des.fleet_vehicle_id.ids
    #             for _id in self.ids:
    #                 if _id in fleet_vehicle_id:
    #                     fleet_vehicle_id.remove(_id)
    #             value_write = {'fleet_vehicle_id': [[6, False, fleet_vehicle_id]]}
    #             pro_des.with_context(FROM_FLEET=False).write(value_write)
    #     return res
    #
    # @api.model
    # def create(self, value):
    #     res = super(FleetFleet, self).create(value)
    #     if res:
    #         for product in res.product_ids:
    #             fleet_vehicle_id = product.fleet_vehicle_id.ids
    #             fleet_vehicle_id.extend(res.ids)
    #             value_write = {'fleet_vehicle_id': [[6, False, fleet_vehicle_id]]}
    #             product.with_context(FROM_FLEET=False).write(value_write)
    #     return res

    def _compute_count_all(self):
        for record in self:
            record.service_count = self.env['fleet.repair'].search_count([('fleet_repair_line', 'in', record.id)])

    @api.multi
    def button_view_service(self):
        list = []
        context = dict(self._context or {})
        repair_ids = self.env['fleet.repair'].search([('fleet_repair_line', '=', self.id)])
        for repair in repair_ids:
            list.append(repair.id)
        return {
            'name': _('Các dịch vụ'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'fleet.repair',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', list)],
            'context': context,
        }


FleetFleet()

#
# class FleetServiceType(models.Model):
#
#     _inherit = "fleet.service.type"
#
#     product_ids = fields.Many2many("product.template", "fleet_vehicle_id", string="Product ")
#
#     @api.multi
#     def write(self, value):
#         old_product_ids = self.product_ids
#         res = super(FleetFleet, self).write(value)
#         if res and "product_ids" in value and self.env.context.get('FROM_FLEET', True):
#             for product in self.product_ids:
#                 if product not in old_product_ids:
#                     fleet_service_type_id = product.fleet_service_type_id.ids
#                     fleet_service_type_id.extend(self.ids)
#                     value_write = {'fleet_service_type_id': [[6, False, fleet_service_type_id]]}
#                     product.with_context(FROM_FLEET=False).write(value_write)
#             product_destroy = [x for x in old_product_ids if x not in self.product_ids]
#             for pro_des in product_destroy:
#                 fleet_service_type_id = pro_des.fleet_service_type_id.ids
#                 for _id in self.ids:
#                     if _id in fleet_service_type_id:
#                         fleet_service_type_id.remove(_id)
#                 value_write = {'fleet_service_type_id': [[6, False, fleet_service_type_id]]}
#                 pro_des.with_context(FROM_FLEET=False).write(value_write)
#         return res
#
#     @api.model
#     def create(self, value):
#         res = super(FleetFleet, self).create(value)
#         if res:
#             for product in res.product_ids:
#                 fleet_vehicle_id = product.fleet_vehicle_id.ids
#                 fleet_vehicle_id.extend(res.ids)
#                 value_write = {'fleet_vehicle_id': [[6, False, fleet_vehicle_id]]}
#                 product.with_context(FROM_FLEET=False).write(value_write)
#         return res
#
#
# FleetServiceType()


class FleetVehicleVersion(models.Model):
    _name = "fleet.vehicle.version"
    _description = "Fleet Vehicle Version"

    name = fields.Char(required=True)
    description = fields.Char()
