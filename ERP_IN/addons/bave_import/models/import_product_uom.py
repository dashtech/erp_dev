# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime,timedelta
import pytz


class ImportProductUom(models.TransientModel):
    _name = 'import.product.uom'
    _inherits = {'ir.attachment': 'attachment_id'}
    _import_model_name = 'product.uom'
    _import_date_format = '%d-%m-%Y'

    template_file_url = fields.Char(compute='_compute_template_file_url',
                                    default=lambda self:
                                    self.env['ir.config_parameter'].
                                    get_param('web.base.url') +
                                    '/bave_import/static/import_template/'
                                    'import_product_uom.xlsx')

    @api.multi
    def _compute_template_file_url(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        url = base_url + '/bave_import/static/import_template/import_product_uom.xlsx'
        for ip in self:
            ip.template_file_url = url

    def import_product_uom(self):
        content = self.get_value_from_excel_row()
        if content['atts_create']:
            for att in content['atts_create']:
                self.env['product.uom'].create(att)
        return True

    @api.multi
    def get_value_from_excel_row(self):
        excel_data = self.env['read.excel'].read_file(data=self.datas, sheet="Sheet1", path=False)
        uom_model = self.env['product.uom']
        if excel_data:
            catg_data = {}
            atts_create = []
            row_count = 1
            for i in excel_data[1:]:
                row_count += 1
                if not i[0]:
                    raise UserError(_('Uom name can not empty, Row %s - Column A') % row_count)
                if not i[1]:
                    raise UserError(_('Category UOM can not empty, Row %s - Column B') % row_count)
                if not i[2]:
                    raise UserError(_('Uom type can not empty, Row %s - Column C') % row_count)
                if not i[3]:
                    raise UserError(_('Rounding can not empty, Row %s - Column D') % row_count)

                psql = '''select id from '''

                parent_uom_id = self.env['product.uom.categ'].sudo().search(
                    [('name', '=', i[1].encode('utf-8').strip())])
                if not parent_uom_id:
                    raise UserError(_('Category UOM does not exist, Row %s - Column B') % row_count)

                x_type_1 = u'Lớn hơn đơn vị đo lường gốc'
                x_type_2 = u'Đơn vị gốc của nhóm này'
                x_type_3 = u'Nhỏ hơn đơn vị gốc của nhóm này'

                x_type = ''
                if i[2].encode('utf-8').strip().lower() == x_type_1.encode('utf-8').strip().lower():
                    x_type = 'bigger'
                elif i[2].encode('utf-8').strip().lower() == x_type_2.encode('utf-8').strip().lower():
                    x_type = 'reference'
                elif i[2].encode('utf-8').strip().lower() == x_type_3.encode('utf-8').strip().lower():
                    x_type = 'smaller'

                if not x_type:
                    raise UserError(_('Type UOM can not empty, Row %s - Column C') % row_count)

                atts_create.append({
                    'name': i[0],
                    'category_id': parent_uom_id.id if parent_uom_id else False,
                    'uom_type': x_type,
                    'rounding': i[3]
                })
            catg_data['atts_create'] = atts_create
            # catg_data['atts_write'] = atts_write
            return catg_data
