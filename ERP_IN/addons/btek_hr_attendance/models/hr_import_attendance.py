# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
import pytz
from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx


class HrAttendanceImport(models.Model):
    _name = 'hr.attendance.import'
    _inherits = {'ir.attachment': 'attachment_id'}

    attachment_id = fields.Many2one('ir.attachment', string=u'Danh sách ra vào',
                                    ondelete='cascade')
    template_file = fields.Char(compute='_compute_template_file',
                                default=lambda self:
                                self.env['ir.config_parameter'].get_param('web.base.url') +
                                '/btek_hr_attendance/static/template/Attendance.xlsx')

    error_log = fields.Char(default='Some records import error, Click button to download import error file')

    @api.multi
    def _compute_template_file(self):
        Parameters = self.env['ir.config_parameter']
        base_url = Parameters.get_param('web.base.url')
        url = base_url + '/btek_hr_attendance/static/template/Attendance.xlsx'
        for import_ds in self:
            import_ds.template_file = url

    def import_attendance(self):
        content = self.get_file_content()
        if content['atts']:
            for att in content['atts']:
                check_record = self.env['hr.attendance'].sudo().search([
                    ('employee_id', '=', att['employee_id']),
                    ('check_in', '=', att['check_in']),
                    ('check_out', '=', att['check_out'])
                ])
                if not check_record:
                    res_update = self.env['hr.attendance'].sudo().create(att)

        if content['atts_fail']:
            action = self.env.ref('btek_hr_attendance.import_failed_action').read()[0]
            action['res_id'] = self.id
            return action
            # return self.export_report(content['atts_fail'])

    def get_file_content(self):
        res = self.env['read.excel'].read_file(data=self.datas, sheet="Sheet1", path=False)
        user_tz = self.env.user.tz or str(pytz.utc)
        tz_now = datetime.now(pytz.timezone(user_tz))
        difference = int(tz_now.utcoffset().total_seconds() / 60 / 60)
        if res:
            attendance = {}
            atts = []
            atts_fail = []
            for i in res[1:]:
                if not i[1]:
                    raise UserError(u'Tên viết tắt không được bỏ trống')

                employee_id = self.env['hr.employee'].sudo().search(
                    [('code_name', '=', i[1])])
                if not employee_id:
                    atts_fail.append(i)
                    continue

                check_in = check_out = False
                if i[2]:
                    date_in = str(datetime.strptime(i[2], '%d/%m/%Y %H:%M:%S'))
                    check_in = str(datetime.strptime(date_in, '%Y-%m-%d %H:%M:%S') \
                               + timedelta(hours=-difference))
                if i[3]:
                    date_out = str(datetime.strptime(i[3], '%d/%m/%Y %H:%M:%S'))
                    check_out = str(datetime.strptime(date_out, '%Y-%m-%d %H:%M:%S') \
                               + timedelta(hours=-difference))

                atts.append({
                    'employee_id': employee_id.id,
                    'check_in': check_in ,
                    'check_out':  check_out,
                })
            attendance['atts'] = atts
            attendance['atts_fail'] = atts_fail
            return attendance

    @api.multi
    def export_report(self, fail_lst):
        datas = {'ids': self.ids}
        datas['model'] = 'hr.attendance.import'
        datas['form'] = self.read()[0]
        datas['fail_lst'] = fail_lst

        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'btek_hr_attendance.import_failed.xlsx',
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
            'font_size': 18,
            'font_name': 'Times New Roman',
        })
        table_header = wb.add_format({
            'bold': 1,
            'text_wrap': 1,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'font_name': 'Times New Roman',
        })
        table_row_center = wb.add_format({
            'text_wrap': 1,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'font_name': 'Times New Roman',
        })
        table_row_right = wb.add_format({
            'text_wrap': 1,
            'align': 'right',
            'valign': 'vcenter',
            'border': 1,
            'num_format': '#,##0',
            'font_name': 'Times New Roman',
        })
        row_date_default = wb.add_format({
            'text_wrap': 1,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'font_name': 'Times New Roman',
            'font_size': 11,
            'num_format': 'dd/mm/yyyy'
        })
        wb.formats[0].font_name = 'Arial'
        wb.formats[0].font_size = 12
        ws.set_paper(9)  # A4 210 x 297 mm
        ws.center_horizontally()
        ws.set_margins(left=0.28, right=0.28, top=0.5, bottom=0.5)
        ws.set_landscape()
        ws.set_column(0, 0, 8)
        ws.set_column(1, 1, 15)
        ws.set_column(2, 2, 25)
        ws.set_column(3, 3, 25)

        # ws.merge_range("A1:D3", 'Import Failed', bold)
        if data['atts_fail']:
            row_nums = 1
            ws.write('A{}'.format(row_nums), 'Id', bold)
            ws.write('B{}'.format(row_nums), 'Sort name', bold)
            ws.write('C{}'.format(row_nums), 'Check-in', bold)
            ws.write('D{}'.format(row_nums), 'Check-out', bold)
            row_nums += 1
            for i in data['atts_fail']:
                ws.write('A{}'.format(row_nums), int(i[0]))
                ws.write('B{}'.format(row_nums), i[1])
                ws.write('C{}'.format(row_nums), i[2])
                ws.write('D{}'.format(row_nums), i[3])
                row_nums += 1

import_failed('report.btek_hr_attendance.import_failed.xlsx', 'hr.attendance.import')
