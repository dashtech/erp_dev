# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import pytz

brand_index = 1
model_index = 2
version_index = 3
color_index = 4

MIN_COL_NUMBER = 5


class WizardImportFleetModel(models.TransientModel):
    _name = 'wizard.import.fleet.model'
    _inherits = {'ir.attachment': 'attachment_id'}

    attachment_id = fields.Many2one(
        'ir.attachment', 'Attachment',
        required=True)
    template_file_url = fields.Char(
        compute='_compute_template_file_url',
        default=lambda self:self.env['ir.config_parameter'].
        get_param('web.base.url') +
        '/car_repair_master_data/static/import_template/'
        'import_fleet_model.xls')
    message_success = fields.Char()

    @api.multi
    def _compute_template_file_url(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        url = base_url + '/car_repair_master_data/static/import_template/import_fleet_model.xls'
        for ip in self:
            ip.template_file_url = url

    def format_name(self, name):
        if not name:
            return name
        return name.strip().lower()

    @api.multi
    def import_fleet_model(self):
        # read excel file
        data = self.datas
        sheet = False

        user = self.env.user
        path = '/import_fleet_model_' \
               + user.login + '_' + str(
            self[0].id) + '_' + str(
            datetime.now()) + '.xls'
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

        # Get db data dict for many2one, many2many field: dict with key = name,
        # value = ID db
        brand_dict, model_dict, \
        version_dict, color_dict = \
            self.get_db_data(excel_data)

        model_tree = self.build_model_tree(excel_data)

        brand_ids = self.create_brand(model_tree, brand_dict)

        model_ids = self.create_model(
            model_tree, brand_dict, model_dict,
            version_dict, color_dict)
        message_success = (_(u'Đã nhập thành công {} dòng xe').format(len(model_ids)))

        self.message_success = message_success
        action_obj = self.env.ref('car_repair_master_data.wizard_import_fleet_model_message_form_view_action')
        action = action_obj.read([])[0]
        action['res_id'] = self.id

        return action

    @api.multi
    def verify_excel_data(self, excel_data):
        row_count = 1

        for row in excel_data:
            row_count += 1

            for field_index in [(brand_index, _('brand')),
                          (model_index, _('model')),
                          (version_index, _('version')),
                          (color_index, _('color'))]:
                index = field_index[0]
                label = field_index[1]
                if row[index]:
                    try:
                        row[index] = unicode(row[index]).strip()
                    except:
                        raise UserError(
                            _('Error: row {} {} invalid!').format(
                                row_count, label))
        return True

    @api.multi
    def get_db_data(self, excel_data):
        brand_s = \
            self.env['fleet.vehicle.model.brand'
            ].search_read([], ['name'])
        brand_dict = dict((self.format_name(b['name']), b['id']) for b in brand_s)

        model_s = \
            self.env['fleet.vehicle.model'
            ].search_read([], ['name', 'vehicle_version_id'])
        model_dict = {}
        for m in model_s:
            name = self.format_name(m['name'])
            version_id = m['vehicle_version_id'] and m['vehicle_version_id'][0] or 0
            model_id = m['id']
            model_dict[(name, version_id)] = model_id

        version_s = \
            self.env['fleet.vehicle.version'
            ].search_read([], ['name'])
        version_dict = dict((v['name'], v['id']) for v in version_s)

        color_s = \
            self.env['fleet.vehicle.color'
            ].search_read([], ['name', 'color_code'])

        color_dict = {}
        for c in color_s:
            name = c['name']
            code = c['color_code'] or ''
            color_dict[name + code] = c['id']

        return brand_dict, model_dict, version_dict, color_dict

    def build_model_tree(self, excel_data):
        model_tree = {}
        current_brand = ''
        for row in excel_data:
            if row[brand_index]:
                current_brand = self.format_name(row[brand_index])
                model_tree[current_brand] = {}

            if row[model_index]:
                vehicle_model = self.format_name(row[model_index])

                version = row[version_index]
                version_list = []
                if version:
                    version_list = version.split(',')

                color = row[color_index]
                color_list = []
                if color:
                    color_list = color.split(',')

                model_tree[current_brand][vehicle_model] = {
                    'vehicle_model_name': row[model_index].strip(),
                    'version': version_list,
                    'color': color_list,
                }
        return model_tree

    def create_brand(self, model_tree, brand_dict):
        brand_ids = []

        for brand in model_tree.keys():
            if not brand:
                continue

            if brand_dict.get(brand, False):
                continue

            brand_id = self.env['fleet.vehicle.model.brand'].create(
                {
                    'name': brand.title()
                }
            )
            brand_dict[brand] = brand_id.id
            brand_ids.append(brand_id.id)
        return brand_ids

    def create_version(self, version_list, version_dict):
        version_ids = []
        if not version_list:
            return []

        for version_name in version_list:
            version_id = version_dict.get(version_name, False)
            if version_id:
                version_ids.append(version_id)
                continue

            version_id = self.env['fleet.vehicle.version'].create({
                'name': version_name
            })
            version_ids.append(version_id.id)
            version_dict[version_name] = version_id.id
        return version_ids

    def create_color(self, color_list, color_dict):
        color_ids = []
        if not color_list:
            return []

        for color_name in color_list:
            color_id = color_dict.get(color_name, False)
            if color_id:
                color_ids.append(color_id)
                continue

            color_name_list = color_name.split('#')
            name = color_name
            color_code = False
            if len(color_name_list) > 1:
                name = color_name_list[0]
                color_code = color_name_list[1]

            color_id = self.env['fleet.vehicle.color'].create({
                'name': name,
                'color_code': u'#{}'.format(color_code or '')
            })
            color_ids.append(color_id.id)
            color_dict[color_name] = color_id.id
        return color_ids

    def create_model(
            self, model_tree, brand_dict,
            model_dict, version_dict, color_dict):
        model_ids = []
        for brand in model_tree.keys():
            brand_id = brand_dict.get(brand, False)
            if not brand_id:
                continue

            for model in model_tree[brand].keys():
                if model_dict.get(model, False):
                    continue
                vehicle_model_name = model_tree[brand][model]['vehicle_model_name']
                version = model_tree[brand][model]['version']

                version_ids = self.create_version(version, version_dict)
                if not version_ids:
                    version_ids.append(False)

                color = model_tree[brand][model]['color']
                color_ids = self.create_color(color, color_dict)

                for version_id in version_ids:
                    v = version_id or 0
                    key = (model, v)
                    model_id = model_dict.get(key, False)
                    if model_id:
                        continue

                    vals = {
                        'name': vehicle_model_name,
                        'brand_id': brand_id,
                        'vehicle_version_id': version_id,
                        'car_color_ids': [(6, False, color_ids)]
                    }

                    model_id = self.env['fleet.vehicle.model'
                    ].create(vals)
                    model_ids.append(model_id)

        return model_ids
