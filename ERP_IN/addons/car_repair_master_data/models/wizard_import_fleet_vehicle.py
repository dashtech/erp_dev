# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
from copy import deepcopy
import xlsxwriter
import base64
import os
import tempfile

partner_code_index = 0
partner_name_index = 1
model_index = 2
license_plate_index = 3
location_index = 4
type_id_index = 5
color_id_index = 6
vin_sn_index = 7
chassis_number_index = 8
odometer_index = 9
car_value_index = 10
seats_index = 11
doors_index = 12

MIN_COL_NUMBER = 13


class WizardImportFleetVehicle(models.TransientModel):
    _name = 'wizard.import.fleet.vehicle'
    _inherits = {'ir.attachment': 'attachment_id'}

    attachment_id = fields.Many2one(
        'ir.attachment', 'Attachment',
        required=True)
    template_file_url = fields.Char(
        compute='_compute_template_file_url',
        default=lambda self:self.env['ir.config_parameter'].
        get_param('web.base.url') +
        '/car_repair_master_data/static/import_template/'
        'fleet_vehicle_import_template.xlsx')
    f_name = fields.Char()
    return_error_file = fields.Binary(attachment=True)

    @api.model
    def create(self, vals):
        vals['f_name'] = _('Return_error.xlsx')
        return super(WizardImportFleetVehicle, self).create(vals)

    @api.multi
    def _compute_template_file_url(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        url = base_url + '/car_repair_master_data/static/import_template/fleet_vehicle_import_template.xlsx'
        for ip in self:
            ip.template_file_url = url

    def format_name(self, name):
        if not name:
            return name
        return name.strip().lower()

    @api.multi
    def import_fleet_vehicle(self):
        # read excel file
        data = self.datas
        sheet = False

        user = self.env.user
        path = '/import_fleet_vehicle_' \
               + user.login + '_' + str(
            self[0].id) + '_' + str(
            datetime.now()) + '.xlsx'
        path = path.replace(' ', '_')

        read_excel_obj = self.env['read.excel']
        excel_data = read_excel_obj.read_file(data, sheet, path)

        # check content excel data
        if len(excel_data) < 3:
            raise UserError(_('Error: Cannot import empty file!'))

        header_row = deepcopy(excel_data[0])
        header_row.append(_('Error description'))
        excel_data_copy = deepcopy(excel_data)
        return_excel_data = []

        # delete header excel (first line in file)
        del excel_data[0]

        # check number column excel file
        if len(excel_data[1]) < MIN_COL_NUMBER:
            raise UserError(_(
                'Error: Format file incorrect, you must import file have at least {} column!').format(
                MIN_COL_NUMBER))

        # check format data in excell file(unicode, str, ...)
        error_dict = self.verify_excel_data(excel_data)

        # Get db data dict for many2one, many2many field: dict with key = name,
        # value = ID db
        license_plate_s, partner_dict, \
        model_dict, type_dict, color_dict= \
            self.get_db_data(excel_data)

        value_list = []
        index = 1
        for row in excel_data:
            index += 1

            if error_dict.get(str(index), False):
                error_row = deepcopy(row)

                error_item = error_dict.get(str(index))
                error_text = u','.join([u'{}:{}'.format(e, error_item[e]) for e in error_item.keys()])
                error_row.append(error_text)
                return_excel_data.append(error_row)
                # print '--------------------{}'.format(index)
                # print error_row
                continue

            value = self.get_value_from_excel_data(
                row, index, license_plate_s, partner_dict,
                model_dict, type_dict, color_dict, error_dict
            )

            if error_dict.get(str(index), False):
                error_row = deepcopy(row)

                error_item = error_dict.get(str(index))
                error_text = u','.join(
                    [u'{}:{}'.format(e, error_item[e]) for e in
                     error_item.keys()])
                error_row.append(error_text)
                return_excel_data.append(error_row)

                # print '--------------------{}'.format(index)
                # print error_row
                continue

            value_list.append(value)

        # print 'error'
        # for row in error_dict.keys():
        #     print '----------{}'.format(row)
        #     for f in error_dict[row].keys():
        #         print u'{}: {}'.format(f, error_dict[row][f])
        #
        # print 'value'
        # for v in value_list:
        #     print v

        res = self.create_record(value_list)

        if return_excel_data:
            return self.return_error_excel(header_row, return_excel_data)
        return res

    def process_error(self, row_count, error_text, label, error_dict):
        if not error_dict.get(str(row_count), False):
            error_dict[str(row_count)] = {}
        error_text = u'{},{}'.format(error_dict[str(row_count)].get(label, ''), error_text)
        error_dict[str(row_count)][label] = error_text

    @api.multi
    def verify_excel_data(self, excel_data):
        def char_format(source):
            return unicode(source).strip()
        def float_format(source):
            return float(source)
        def int_format(source):
            return int(source)

        error_dict = {}

        row_count = 1

        license_plate_list = []

        for row in excel_data:
            row_count += 1

            for field_index in [(char_format,partner_code_index, _('customer code'), False),
                                (char_format,partner_name_index , _('customer name'), False),
                                (char_format,model_index, _('car model'), True),
                                (char_format,license_plate_index, _('car plate'), True),
                                (char_format,location_index, _('Location'), False),
                                (char_format,type_id_index, _('type'), False),
                                (char_format,color_id_index, _('color'), False),
                                (char_format,vin_sn_index, _('vin number'), False),
                                (char_format,chassis_number_index, _('chassis number'), False),
                                (float_format, odometer_index, _('odometer'), False),
                                (float_format,car_value_index, _('Car value'), False),
                                (int_format,seats_index, _('Seats'), False),
                                (int_format,doors_index, _('doors'), False),
                                ]:
                format_fnct = field_index[0]
                index = field_index[1]
                label = field_index[2]
                required = field_index[3]

                if required and not row[index]:
                    error_text = _('Error: row {} {} is blank!').format(
                            row_count, label
                        )
                    self.process_error(
                        row_count, error_text, label, error_dict)

                if row[index]:
                    try:
                        row[index] = format_fnct(row[index])
                    except:
                        error_text = _('Error: row {} {} invalid!').format(
                            row_count, label)
                        self.process_error(
                            row_count, error_text, label, error_dict)

            if row[license_plate_index] in license_plate_list:
                error_text = _(u'Error: license plate {} in row {} exist on other row'
                               ).format(row[license_plate_index], row_count)
                self.process_error(
                    row_count, error_text, label, error_dict)

            license_plate_list.append(row[license_plate_index])
        return error_dict

    @api.multi
    def get_db_data(self, excel_data):
        partner_name_list = []
        model_list = []
        license_plate_list = []

        for row in excel_data:
            partner_name = self.format_name(row[partner_name_index])
            model = row[model_index]
            license_plate = row[license_plate_index]

            partner_name_list.append(partner_name)
            model_list.append(model)
            license_plate_list.append(license_plate)

        vehicle_s = \
            self.env['fleet.vehicle'].search_read(
                [('license_plate', 'in', license_plate_list)],
                ['license_plate']
            )
        license_plate_s = \
            [vehicle['license_plate'] for vehicle in vehicle_s]

        partner_name_where = u"','".join(partner_name_list)
        query = u"""
            select id, name, code from res_partner
            where trim(lower(name)) in ('{}')
        """.format(partner_name_where)
        self.env.cr.execute(query)

        partner_dict = {}

        for p in self.env.cr.dictfetchall():
            partner_name = self.format_name(p['name'])
            partner_dict[partner_name] = p['id']
            code = p['code'] or ''
            code = self.format_name(code)
            partner_dict[(partner_name, code)] = p['id']
            partner_dict[partner_name] = p['id']
            partner_dict[code] = p['id']

        model_s = \
            self.env['fleet.vehicle.model'
            ].search([]).name_get()
        model_dict = dict((self.format_name(model[1]), model[0]) for model in model_s)
        model_s = \
            self.env['fleet.vehicle.model'
            ].search([])
        for model in model_s:
            model_dict[self.format_name(model.name)] = model.id

            model_name = u'{}/{}'.format(model.brand_id.name, model.name)
            model_dict[self.format_name(model_name)] = model.id

            if model.vehicle_version_id:
                model_name = u'{}/{}'.format(model.name, model.vehicle_version_id.name)
                model_dict[self.format_name(model_name)] = model.id

        type_s = \
            self.env['fleet.vehicle.type'
            ].search([]).name_get()
        type_dict = dict((self.format_name(type[1]), type[0]) for type in type_s)
        color_s = \
            self.env['fleet.vehicle.color'
            ].search([]).name_get()
        color_dict = dict((self.format_name(c[1]), c[0]) for c in color_s)

        return license_plate_s,partner_dict,model_dict, type_dict, color_dict

    def get_value_from_excel_data(
            self, row, index, license_plate_s, partner_dict,
            model_dict, type_dict, color_dict, error_dict):

        license_plate = row[license_plate_index]
        if license_plate in license_plate_s:
            error_text = _(
                u'Error: license plate {} already exist!'
            ).format(license_plate)
            self.process_error(
                index, error_text, _('car plate'), error_dict)

        value = {
            'license_plate': row[license_plate_index],
            'location': row[location_index] or False,
            'vin_sn': row[vin_sn_index] or False,
            'chassis_number': row[chassis_number_index] or False,
            'odometer': row[odometer_index] or False,
            'car_value': row[car_value_index] or False,
            'seats': row[seats_index]or False,
            'doors': row[doors_index] or False
        }
        partner_code = self.format_name(row[partner_code_index]) or ''
        partner_name = self.format_name(row[partner_name_index]) or ''

        key = (partner_name, partner_code)
        driver_id = partner_dict.get(key, False)
        if not driver_id and partner_code:
            driver_id = partner_dict.get(partner_code, False)
        if not driver_id and partner_name:
            driver_id = partner_dict.get(partner_name, False)

        if not driver_id:
            error_text = _('Error: Cannot find car owner {} in row {}'
                           ).format(row[partner_name_index], index)
            self.process_error(
                index, error_text, _('customer name'), error_dict)

        value['driver_id'] = driver_id

        model_name = self.format_name(row[model_index])
        model_id = model_dict.get(model_name, False)
        if not model_id:
            error_text = _('Error: Cannot find car model {} in row {}'
                           ).format(row[model_index], index)
            self.process_error(
                index, error_text, _('car model'), error_dict)

        value['model_id'] = model_id

        if row[type_id_index]:
            type_name = self.format_name(row[type_id_index])
            type_id = type_dict.get(type_name, False)
            if not type_id:
                error_text = _(u'Error: Cannot find car type {} in row {}'
                               ).format(row[car_value_index], index)
                self.process_error(
                    index, error_text, _('car type'), error_dict)

            value['type_id'] = type_id

        if row[color_id_index]:
            color_name = self.format_name(row[color_id_index])
            color_id = color_dict.get(color_name, False)
            if not color_id:
                error_text = _(u'Error: Cannot find car color {} in row {}'
                               ).format(row[color_id_index], index)
                self.process_error(
                    index, error_text, _('car type'), error_dict)

            value['color_id'] = color_id

        return value

    def create_record(self, value_list):
        res = []
        for value in value_list:
            vehicle_id = self.env['fleet.vehicle'].create(value)
            res.append(vehicle_id)
        return res

    def return_error_excel(self, header_row, return_excel_data):
        filename = 'return_error_fleet_vehicle_' \
               + self.env.user.login + '_' + str(
            self[0].id) + '_' + str(
            datetime.now())
        filename = filename.replace(' ', '_')
        filename = filename.replace(':', '_')
        filename = filename.replace('.', '_') + '.xlsx'
        temppath = tempfile.gettempdir()
        filepath = os.path.join(temppath, filename)

        workbook = xlsxwriter.Workbook(filepath)
        worksheet = workbook.add_worksheet()

        worksheet.set_column('A:A', 10)
        worksheet.set_column('B:B', 15)
        worksheet.set_column('C:C', 12)
        worksheet.set_column('D:D', 12)
        worksheet.set_column('E:E', 12)
        worksheet.set_column('F:F', 12)
        worksheet.set_column('G:G', 12)
        worksheet.set_column('H:H', 12)
        worksheet.set_column('I:I', 12)
        worksheet.set_column('J:J', 12)
        worksheet.set_column('K:K', 12)
        worksheet.set_column('L:L', 12)
        worksheet.set_column('M:M', 12)
        worksheet.set_column('N:N', 34)

        normal_normal = workbook.add_format(
            {
                'valign': 'vcenter',
                'num_format': '#,##0',
            }
        )
        normal_normal.set_font_name('Times New Roman')
        normal_normal.set_text_wrap()
        normal_normal.set_top()
        normal_normal.set_bottom()
        normal_normal.set_left()
        normal_normal.set_right()

        normal_header = workbook.add_format(
            {
                'bold': True,
                'valign': 'vcenter',
                'num_format': '#,##0',
            }
        )
        normal_header.set_font_name('Times New Roman')
        normal_header.set_text_wrap()
        normal_header.set_top()
        normal_header.set_bottom()
        normal_header.set_left()
        normal_header.set_right()
        normal_header.set_fg_color('blue')

        col = 0
        for header_item in header_row:
            worksheet.write(0, col, header_item, normal_header)
            col += 1

        row_index = 1
        for row in return_excel_data:
            col = 0
            for item in row:
                worksheet.write(row_index, col, item, normal_normal)
                col += 1
            row_index += 1

        workbook.close()

        f = open(filepath, "rb")
        encoded_string = base64.b64encode(f.read())
        f.close()

        return_error_vals = {
            'return_error_file': encoded_string,
        }
        self.write(return_error_vals)

        action_obj = self.env.ref(
            'car_repair_master_data.wizard_import_fleet_vehicle_return_error_form_view_action')
        action = action_obj.read([])[0]
        action['res_id'] = self.id
        return action
