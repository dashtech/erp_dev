# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime

partner_code_index = 0
partner_name_index = 1
name_index = 2
license_plate_index = 3
date_order_index = 4
product_service_code_index = 5
validity_date_index = 6
service_type_index = 7
description_index = 8
user_index = 9
price_unit_index = 10
index_index = 10

MIN_COL_NUMBER = 11


class WizardImportCarRepairHistory(models.TransientModel):
    _name = 'wizard.import.car.repair.history'
    _inherits = {'ir.attachment': 'attachment_id'}

    attachment_id = fields.Many2one(
        'ir.attachment', 'Attachment',
        required=True)
    template_file_url = fields.Char(
        compute='_compute_template_file_url',
        default=lambda self:self.env['ir.config_parameter'].
        get_param('web.base.url') +
        '/car_repair_master_data/static/import_template/'
        'import_car_repair_history.xls')

    @api.multi
    def _compute_template_file_url(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        url = base_url + '/car_repair_master_data/static/import_template/import_car_repair_history.xls'
        for ip in self:
            ip.template_file_url = url

    @api.multi
    def import_car_repair_history(self):
        # read excel file
        data = self.datas
        sheet = False

        user = self.env.user
        path = '/import_car_repair_history_' \
               + user.login + '_' + str(
            self[0].id) + '_' + str(
            datetime.now()) + '.xlsx'
        path = path.replace(' ', '_')

        read_excel_obj = self.env['read.excel']
        excel_data = read_excel_obj.read_file(data, sheet, path)

        # check content excel data
        if len(excel_data) < 3:
            raise UserError(_('Error: Cannot import empty file!'))

        # delete header excel (first line in file)
        del excel_data[0]

        # check number column excel file
        if len(excel_data[1]) < MIN_COL_NUMBER:
            raise UserError(_(
                'Error: Format file incorrect, you must import file have at least {} column!').format(
                MIN_COL_NUMBER))

        # check format data in excell file(unicode, str, ...)
        self.verify_excel_data(excel_data)

        formated_excel_data = self.formated_excel_data(excel_data)

        # Get db data dict for many2one, many2many field: dict with key = name,
        # value = ID db
        partner_name_dict, partner_code_dict, \
        license_plate_dict, product_dict, \
        service_type_dict, user_dict = \
            self.get_db_data(formated_excel_data)

        value_list = []
        index = 1
        for row in formated_excel_data:
            index += 1
            value = self.get_value_from_excel_data(
                row, partner_name_dict, partner_code_dict, \
               license_plate_dict, product_dict, \
               service_type_dict, user_dict
            )
            value_list.append(value)

        res = self.create_record(value_list)
        return res

    @api.multi
    def verify_excel_data(self, excel_data):
        def char_format(source):
            return unicode(row[index]).strip()
        def date_format(source):
            return datetime.strptime(unicode(row[index]).strip(), '%d/%m/%Y').strftime('%Y-%m-%d')
        def float_format(source):
            return float(source)
        def int_format(source):
            return int(source)

        row_count = 1
        for row in excel_data:
            row_count += 1

            for field_index in [
                (char_format, partner_code_index, _('Customer code'), False),
                (char_format, partner_name_index, _('Customer name'), False),
                (char_format, name_index, _('repair number'), False),
                (char_format, license_plate_index, _('License plates'), False),
                (date_format, date_order_index, _('Car in date'), False),
                (char_format, product_service_code_index, _('Product,service code'), False),
                (date_format, validity_date_index, _('Validity date'), False),
                (char_format, service_type_index, _('Service type'), False),
                (char_format, description_index, _('Customer request'), False),
                (char_format, user_index, _('Assignee'), False),
                (float_format, price_unit_index, _('Price unit'), False)
                                ]:
                format_fnct = field_index[0]
                index = field_index[1]
                label = field_index[2]
                required = field_index[3]

                if required and not row[index]:
                    raise UserError(
                        _('Error: row {} {} is blank!').format(
                            row_count, label
                        )
                    )

                if row[index]:
                    try:
                        row[index] = format_fnct(row[index])
                    except:
                        raise UserError(
                            _('Error: row {} {} invalid!').format(
                                row_count, label))

        return True

    def formated_excel_data(self, excel_data):
        formated_excel_dict = {}
        current_license_plate = False

        name_list = []

        index = 1
        for row in excel_data:
            index += 1
            license_plate = row[license_plate_index]
            if license_plate:
                current_license_plate = license_plate

                if not row[license_plate_index]:
                    raise UserError(_('Error row {} license plate blank!').format(index))
                if not row[date_order_index]:
                    raise UserError(_('Error row {} order date blank!').format(index))
                if not row[user_index]:
                    raise UserError(_('Error row {} assignee blank!').format(index))
                if not row[partner_code_index] and not row[partner_name_index]:
                    raise UserError(_('Error row {} customer name and customer code blank!').format(index))
            if row[name_index]:
                name_list.append(row[name_index])

            if not formated_excel_dict.get(current_license_plate, False):
                formated_excel_dict[current_license_plate] = \
                    {
                        'name': row[name_index],
                        'partner_code': row[partner_code_index],
                        'partner_name': row[partner_name_index],
                        'license_plate': row[license_plate_index],
                        'date_order': row[date_order_index],
                        'product_service_code': [],
                        'validity_date': row[validity_date_index],
                        'service_type': row[service_type_index],
                        'description': row[description_index],
                        'user': row[user_index],
                        'index': index
                     }
            product_service_code = row[product_service_code_index] or ''
            price_unit = row[price_unit_index] or 0
            if product_service_code:
                formated_excel_dict[current_license_plate][
                    'product_service_code'].append({
                    'code': product_service_code,
                    'price_unit': price_unit,
                    'index': index,
                })
        formated_excel_data = []
        for license_plate in formated_excel_dict.keys():
            row = formated_excel_dict[license_plate]
            formated_excel_data.append(
                [
                    row['partner_code'],
                    row['partner_name'],
                    row['name'],
                    row['license_plate'],
                    row['date_order'],
                    row['product_service_code'],
                    row['validity_date'],
                    row['service_type'],
                    row['description'],
                    row['user'],
                    row['index'],
                ]
            )

        duplicate_orders = self.env['sale.order'].search(
            [('name', 'in', name_list)])

        if duplicate_orders:
            raise UserError(_('Error: order name "{}" already exists!').format(
                u','.join(duplicate_orders.mapped('name'))
            ))

        return formated_excel_data

    @api.multi
    def get_db_data(self, formated_excel_data):
        partner_code_list = []
        partner_name_list = []
        license_plate_list = []
        product_list = []
        service_type_list = []

        # partner_code_dict, partner_name_dict, vehicle_dict, \
        # product_dict, service_type_dict, user_dict

        for row in formated_excel_data:
            partner_name = row[partner_name_index]
            partner_code = row[partner_code_index]
            license_plate = row[license_plate_index]
            product_service_code = row[product_service_code_index]
            service_type = row[service_type_index]

            partner_code_list.append(partner_code)
            partner_name_list.append(partner_name)
            license_plate_list.append(license_plate)
            product_list.extend([product['code'] for product in product_service_code])
            service_type_list.append(service_type)

        partner_s = \
            self.env['res.partner'
            ].search_read([('name', 'in', partner_name_list)], ['name'])
        partner_name_dict = dict((p['name'], p['id']) for p in partner_s)

        partner_s = \
            self.env['res.partner'
            ].search_read([('code', 'in', partner_code_list)], ['code'])
        partner_code_dict = dict((p['code'], p['id']) for p in partner_s)

        vehicle_s = \
            self.env['fleet.vehicle'
            ].search_read([('license_plate', 'in', license_plate_list)],
                          ['license_plate'])
        license_plate_dict = dict((v['license_plate'], v['id']) for v in vehicle_s)

        product_s = \
            self.env['product.product'
            ].search([('default_code', 'in', product_list)])
        product_dict = dict((p.default_code, p) for p in product_s)

        service_type_s = \
            self.env['service.type'
            ].search_read([('name', 'in', service_type_list)],
                          ['name'])
        service_type_dict = dict((s['name'], s['id']) for s in service_type_s)

        user_s = self.env['res.users'].search([])
        user_dict = dict((u.name, u.id) for u in user_s)

        return partner_name_dict, partner_code_dict, \
               license_plate_dict, product_dict, \
               service_type_dict, user_dict

    def get_value_from_excel_data(
            self, row, partner_name_dict,
            partner_code_dict, license_plate_dict,
            product_dict, service_type_dict, user_dict):
        index = row[index_index]
        value = {
            'create_form_fleet': True,
            'consignment': False,
            'date_order': row[date_order_index],
            'description': row[description_index],
            'fleet_ids': [(6, False, [])],
            'order_line': [],
            'order_line_service': [],
        }
        if row[name_index]:
            value['name'] = row[name_index]

        partner_name = row[partner_name_index] or ''
        partner_code = row[partner_code_index] or ''

        partner_id = partner_code_dict.get(partner_code, False)
        if not partner_id:
            partner_id = partner_name_dict.get(partner_name)

        if not partner_id:
            raise UserError(
                _(u'Error row {}: cannot find customer with name="{}" or code="{}"!').format(
                    index, partner_name, partner_code))

        value['partner_id'] = partner_id

        license_plate = row[license_plate_index]
        vehicle_id = license_plate_dict.get(license_plate, False)
        if not vehicle_id:
            raise UserError(
                _('Error row {}: cannot find license plate="{}"').format(
                    index, license_plate))
        value['fleet_ids'][0][2].append(vehicle_id)

        product_list = row[product_service_code_index]
        for product_info in product_list:
            product = product_dict.get(product_info['code'], False)
            sub_index = product_info['index']
            if not product:
                raise UserError(
                    _('Error row {}: cannot find product code ="{}"').format(
                        sub_index, product_info['code']))
            line_value = (0, 0, {'product_id': product.id,
                                 'name': product.default_code,
                                 'product_uom_qty': 1,
                                 'product_uom': product.uom_id.id,
                                 'price_unit': product_info['price_unit']
                                 })
            if product.type == 'service':
                value['order_line_service'].append(line_value)
            else:
                value['order_line'].append(line_value)

        if row[validity_date_index]:
            value['validity_date'] = row[validity_date_index]

        if row[service_type_index]:
            service_type_id = \
                service_type_dict.get(row[service_type_index], False)
            if not service_type_id:
                raise UserError(
                    _('Error row {}: cannot find service type "{}"!').format(
                        index, row[service_type_index])
                )
            value['service_type_id'] = service_type_id

        user_id = \
            user_dict.get(row[user_index], False)
        if not user_id:
            raise UserError(
                _('Error row {}: cannot find asignee "{}"!').format(
                    index, row[user_index])
            )
        value['user_id'] = user_id

        return value

    def create_record(self, value_list):
        res = []
        for value in value_list:
            order_id = self.env['sale.order'].create(value)
            order_id.write({'state': 'done'})
            res.append(order_id)
        return res
