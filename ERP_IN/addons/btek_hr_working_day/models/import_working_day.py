# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
import pytz
from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
import re


class HrWorkingDayImport(models.Model):
    _name = 'hr.working.day.import'
    _inherits = {'ir.attachment': 'attachment_id'}

    attachment_id = fields.Many2one('ir.attachment', string=u'Danh sách ra vào',
                                    ondelete='cascade')
    template_file = fields.Char(compute='_compute_template_file',
                                default=lambda self:
                                self.env['ir.config_parameter'].get_param('web.base.url') +
                                '/btek_hr_working_day/static/template/Timesheet012018.xlsx')
    error_log = fields.Char(
        default='Some records import error, Click button to download import error file')

    @api.multi
    def _compute_template_file(self):
        Parameters = self.env['ir.config_parameter']
        base_url = Parameters.get_param('web.base.url')
        url = base_url + '/btek_hr_working_day/static/template/Timesheet012018.xlsx'
        for import_ds in self:
            import_ds.template_file = url

    def get_file_content(self):
        res = self.env['read.excel'].read_file(data=self.datas, sheet="Sheet1", path=False)
        user_tz = self.env.user.tz or str(pytz.utc)
        tz_now = datetime.now(pytz.timezone(user_tz))
        difference = int(tz_now.utcoffset().total_seconds() / 60 / 60)
        if res:
            days_import = {}
            days = []
            days_fail = []
            title = res[0:9]
            date_str = re.findall('\d+', res[4][14])
            if not date_str:
                raise UserError(u'Month, year can not empty!')
            if not date_str[0]:
                raise UserError(u'Month can not empty!')
            if not date_str[1]:
                raise UserError(u'Year can not empty!')
            month = date_str[0]
            year = date_str[1]
            for i in res[9:(len(res)-1)]:
                if not i[2]:
                    raise UserError(u'Tên viết tắt không được bỏ trống')

                employee_id = self.env['hr.employee'].sudo().search(
                    [('code_name', '=', i[2])])
                if not employee_id:
                    days_fail.append(i)
                    continue
                date_num = 1
                for d in i[3:-1]:
                    date = '{}-{}-{}'.format(year, month, date_num)
                    days.append({
                        'employee_id': employee_id.id,
                        'date': str(datetime.strptime(date, '%Y-%m-%d')),
                        'name': 'import',
                        'unit_amount': d or 0,
                    })
                    date_num += 1
            days_import['days'] = days
            days_import['days_fail'] = days_fail
            days_import['title'] = title
            return days_import

    def import_working(self):
        content = self.get_file_content()
        if content['days']:
            for day in content['days']:
                check_record = self.env['hr.working.day.employee'].sudo().search([
                    ('employee_id', '=', day['employee_id']),
                    ('date', '=', day['date']),
                ])
                if not check_record:
                    res_create = self.env['hr.working.day.employee'].sudo().create(day)
                if check_record:
                    for rec in check_record:
                        res_update = self.env['hr.working.day.employee']\
                            .sudo().browse(rec.id).write(day)

        if not content['days_fail']:
            return True

        action = self.env.ref('btek_hr_working_day.working_day_import_failed_action').read()[0]
        action['res_id'] = self.id
        return action

    @api.multi
    def export_report(self, fail_lst):
        datas = {'ids': self.ids}
        datas['model'] = 'hr.working.day.import'
        datas['form'] = self.read()[0]
        datas['fail_lst'] = fail_lst

        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'btek_hr_working_day.import_failed.xlsx',
            'datas': datas,
            'name': _('Import Failed')
        }


class import_failed(ReportXlsx):
    def generate_xlsx_report(self, wb, data, object):
        ws = wb.add_worksheet('Import Failed')
        data = object.get_file_content()
        bold = wb.add_format({
            'bold': 1,
            'text_wrap': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_name': 'Arial',
        })
        center = wb.add_format({
            'align': 'center',
            'text_wrap': 1,
            'valign': 'vcenter',
            'font_name': 'Times New Roman',
        })
        title = wb.add_format({
            'bold': 1,
            'text_wrap': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 10,
            'font_name': 'Times New Roman',
        })
        table_header = wb.add_format({
            'bold': 1,
            'text_wrap': 1,
            'align': 'center',
            'valign': 'vcenter',
            'border': 0,
            'font_name': 'Times New Roman',
            'font_size': 15,
        })
        table_row_center = wb.add_format({
            'text_wrap': 1,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'font_name': 'Times New Roman',
            'border': 1,
        })
        table_row_right = wb.add_format({
            'text_wrap': 1,
            'align': 'right',
            'valign': 'vcenter',
            'border': 1,
            'num_format': '#,##0',
            'font_name': 'Times New Roman',
        })
        row_default = wb.add_format({
            'text_wrap': 1,
            'align': 'left',
            'valign': 'vcenter',
            'border': 0,
            'font_name': 'Times New Roman',
            'font_size': 9.5,
        })
        row_default_border = wb.add_format({
            'text_wrap': 1,
            'align': 'left',
            'valign': 'vcenter',
            'border': 0,
            'font_name': 'Times New Roman',
            'font_size': 9.5,
            'bold': 1,
            'border': 1,
        })
        row_rotation = wb.add_format({
            'text_wrap': 0,
            'rotation': 90,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'font_name': 'Times New Roman',
            'font_size': 9.5,
            'bold': 1,
        })
        wb.formats[0].font_name = 'Times New Roman'
        wb.formats[0].font_size = 9
        ws.set_paper(9)  # A4 210 x 297 mm
        ws.center_horizontally()
        ws.set_margins(left=0.28, right=0.28, top=0.5, bottom=0.5)
        ws.set_landscape()
        ws.set_column(0, 0, 5)
        ws.set_column(1, 1, 15)
        ws.set_column(2, 2, 8)
        ws.set_column(3, 3, 5)
        ws.set_column(4, 4, 5)
        ws.set_column(5, 5, 5)
        ws.set_column(6, 6, 5)
        ws.set_column(7, 7, 5)
        ws.set_column(8, 8, 5)
        ws.set_column(9, 9, 5)
        ws.set_column(10, 10, 5)
        ws.set_column(11, 11, 5)
        ws.set_column(12, 12, 5)
        ws.set_column(13, 13, 5)
        ws.set_column(14, 14, 5)
        ws.set_column(15, 15, 5)
        ws.set_column(16, 16, 5)
        ws.set_column(17, 18, 5)
        ws.set_column(19, 19, 5)
        ws.set_column(20, 20, 5)
        ws.set_column(21, 21, 5)
        ws.set_column(21, 22, 5)
        ws.set_column(23, 23, 5)
        ws.set_column(24, 24, 5)
        ws.set_column(25, 25, 5)
        ws.set_column(26, 26, 5)
        ws.set_column(27, 27, 5)
        ws.set_column(28, 28, 5)
        ws.set_column(29, 29, 5)
        ws.set_column(30, 30, 5)
        ws.set_column(31, 31, 5)
        ws.set_column(32, 32, 5)
        ws.set_column(33, 33, 5)
        ws.set_column(34, 34, 5)

        # ws.merge_range("A1:D3", 'Import Failed', bold)
        tits = data['title']
        ws.merge_range('A1:B1', tits[0][0], row_default)
        ws.merge_range('A2:E2', tits[1][0], row_default)
        ws.merge_range('B4:AG4', tits[3][0], table_header)
        ws.merge_range('O5:S5', tits[4][14], title)
        ws.merge_range('AC7:AG7', tits[6][31], row_default)
        for i in tits[7]:
            ws.write(7, tits[7].index(i), i, row_default_border)
            if tits[7].index(i) == 0:
                ws.merge_range('A8:A11', i, row_default_border)
            if tits[7].index(i) == 1:
                ws.merge_range('B8:B11', i, row_default_border)
            if tits[7].index(i) == 2:
                ws.merge_range('C8:C11', i, row_rotation)
        col = 3
        for i in tits[8][3:-1]:
            ws.merge_range(8, col, 10, col, i, table_row_center)
            col += 1
        row_nums = 11
        for d in data['days_fail']:
            col_nums = 0
            for i in d:
                ws.write(row_nums, col_nums, i or 0, table_row_center)
                col_nums += 1
            row_nums += 1


import_failed('report.btek_hr_working_day.import_failed.xlsx', 'hr.working.day.import')
