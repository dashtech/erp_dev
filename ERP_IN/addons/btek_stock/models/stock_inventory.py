# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime,timedelta
import pytz

# sequence_index = 0
default_code_index = 1
# name_index = 2
stock_location_index = 4
product_qty_index = 5
standart_price_index = 6

MIN_COL_NUMBER = 6


class ImportStockInventoryLine(models.TransientModel):
    _name = 'import.stock.inventory.line'
    _inherits = {'ir.attachment': 'attachment_id'}
    _import_model_name = 'stock.inventory.line'
    # _import_date_format = '%d-%m-%Y'

    stock_inventory_id = fields.Many2one('stock.inventory')
    template_file_url = fields.Char(compute='_compute_template_file_url',
                                    default=lambda self:
                                    self.env['ir.config_parameter'].
                                    get_param('web.base.url') +
                                    '/btek_stock/static/import_template/'
                                    'import_stock_inventory_line.xlsx')

    @api.multi
    def _compute_template_file_url(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        url = base_url + '/btek_stock/static/import_template/import_stock_inventory_line.xlsx'
        for ip in self:
            ip.template_file_url = url

    @api.multi
    def import_stock_inventory_line(self):
        # read excel file
        data = self.datas
        sheet = False

        user = self.env.user
        path = '/import_stock_inventory_template_' \
               + user.login + '_' + str(
            self[0].id) + '_' + str(
            datetime.now()) + '.xls'
        path = path.replace(' ', '_')

        read_excel_obj = self.env['read.excel']
        excel_data = read_excel_obj.read_file(data, sheet, path)

        # check content excel data
        if len(excel_data) < 2:
            raise ValidationError(_('Cannot import empty file!'))

        # delete header excel (2 first line in file)
        del excel_data[0]

        # check number column excel file
        if len(excel_data[1]) < MIN_COL_NUMBER:
            raise ValidationError(_(
                'Format file incorrect, you must import file have at least {} column!').format(
                MIN_COL_NUMBER))

        # check format data in excell file(unicode, str, ...)
        self.verify_excel_data(excel_data)

        # Get db data dict for many2one, many2many field: dict with key = name,
        # value = ID db
        product_dict, stock_location_dict = \
            self.get_db_data(excel_data)

        # Get values list to create from excel data map with db data
        values_list = []

        row_num = 1
        for row in excel_data:
            row_num += 1
            value_product, value_inventory = self.get_value_from_excel_row(
                row, row_num, product_dict,
                stock_location_dict
            )
            values_list.append(value_inventory)
            product = product_dict.get(row[default_code_index], False)
            self.update_record(product['id'], value_product)

        self.create_record(values_list)

        return True

    @api.multi
    def verify_excel_data(self, excel_data):
        row_count = 1

        for row in excel_data:
            row_count += 1

            # try:
            #     row[sequence_index] = row[sequence_index] or 0
            #     row[sequence_index] = int(row[sequence_index])
            # except:
            #     raise UserError(
            #         _('Error: row {} sequence invalid!').format(row_count))

            if not row[default_code_index]:
                raise UserError(
                    _('Error: row {} product code invalid!').format(row_count))

            try:
                row[default_code_index] = unicode(row[default_code_index])
            except:
                raise UserError(
                    _('Error: row {} product code invalid!').format(row_count))

            try:
                row[product_qty_index] = float(row[product_qty_index])
            except:
                raise UserError(
                    _('Error: row {} qty invalid!').format(row_count))

            try:
                row[standart_price_index] = float(row[standart_price_index])
            except:
                raise UserError(
                    _('Error: row {} price invalid!').format(row_count))
        return True

    @api.multi
    def get_db_data(self, excel_data):
        product_code_list = []
        stock_location_list = []
        for row in excel_data:
            product_code = row[default_code_index].strip()
            stock_location = row[stock_location_index].strip()
            if product_code:
                product_code_list.append(product_code)
            if stock_location:
                stock_location_list.append(stock_location)
        product_s = \
            self.env['product.product'].search_read(
                [('default_code', 'in', product_code_list)],
                ['default_code', 'uom_id']
            )

        product_dict = \
            dict((product['default_code'], product) for product in product_s)

        stock_location_s = \
            self.env['stock.location'].search_read(
                [('name', 'in', stock_location_list)],
                ['name']
            )
        stock_location_dict = \
            dict((location['name'], location['id']) for location in stock_location_s)

        return product_dict, stock_location_dict

    @api.multi
    def get_value_from_excel_row(self, row, row_num, product_dict, stock_location_dict):
        value_product = {
            'standard_price': row[standart_price_index]
        }

        value_inventory = {
            'product_qty': row[product_qty_index]
        }

        default_code = row[default_code_index]

        stock_location = row[stock_location_index]

        product = product_dict.get(default_code, False)
        if not product:
            raise UserError(
                _('Error: row {}: cannot find product with product code ="{}"'
                  ).format(row_num, default_code))
        product_id = product['id']
        value_inventory['product_id'] = product_id
        product_uom_id = product['uom_id'][0]
        value_inventory['product_uom_id'] = product_uom_id

        location_id = False
        if stock_location:
            location_id = stock_location_dict.get(stock_location, False)
            if not location_id:
                raise UserError(
                    _('Error: row {} stock location invalid !').format(row_num))
        else:
            raise UserError(
                _('Error: row {} stock location empty !').format(row_num))
        value_inventory['location_id'] = location_id

        return value_product, value_inventory

    # Update standard price of product
    @api.multi
    def update_record(self, product_id, value_product):
        product = self.env['product.product'].browse(product_id)
        product.write(value_product)
        return True

    # Create record from values list
    @api.multi
    def create_record(self, value_list):
        model_name_obj = self.env[self._import_model_name]
        default_value = model_name_obj.default_get([])
        values = {'line_ids': []}

        for value in value_list:
            default_value_copy = default_value.copy()
            default_value_copy.update(value)
            values['line_ids'].append(
                (0, 0, default_value_copy)
            )

        self[0].stock_inventory_id.write(values)

        return True


class PurchaseOrder(models.Model):
    _inherit = 'stock.inventory'

    @api.multi
    def open_wizard_import_stock_inventory_line(self):
        action_obj = self.env.ref(
            'btek_stock.action_import_stock_inventory_line')
        action = action_obj.read()[0]
        action['context'] = {
            'default_stock_inventory_id': self[0].id,
            'default_name': u'[{}]import purchase order line'.format(
                self[0].name)
        }
        return action
