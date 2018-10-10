#!/usr/bin/python
# -*- encoding: utf-8 -*-

from odoo import fields, models, api
from datetime import datetime
import logging
from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx


class FleetRepairXlsx(ReportXlsx):
    _name = 'report.car_repair_industry.fleet_repair_xlsx'

    def generate_xlsx_report(self, workbook, data, repair_obj):
        for repair_id in repair_obj:
            report_name = repair_id.name
            wssheet = workbook.add_worksheet(report_name)
            workbook.formats[0].font_name = 'Times New Roman'
            workbook.formats[0].font_size = 12
            wssheet.set_paper(9)  # A4 210 x 297 mm
            wssheet.set_column(0, 0, 12)
            wssheet.set_column(1, 1, 12)
            wssheet.set_column(2, 2, 12)
            wssheet.set_column(3, 3, 12)
            wssheet.set_column(4, 4, 12)
            wssheet.set_column(5, 5, 12)
            wssheet.set_column(6, 6, 12)
            wssheet.set_column(7, 7, 12)
            wssheet.set_column(8, 8, 12)
            wssheet.set_column(9, 9, 12)

            wssheet.set_row(7, 30)
            wssheet.center_horizontally()
            wssheet.set_margins(left=0.28, right=0.28, top=0.5, bottom=0.5)
            wssheet.set_landscape()
            wssheet.fit_to_pages(1, 1)
            wssheet.hide_gridlines(2)

            # TO DO : Count row to set series
            bold = workbook.add_format({'bold': 1, 'text_wrap': 1})
            price = workbook.add_format({'bold': 1, 'num_format': '#,##0'})
            price_boder = workbook.add_format({'bold': 1, 'num_format': '#,##0', 'border': 1})
            bold_boder = workbook.add_format({'bold': 1, 'border': 1, 'text_wrap': 1})
            signature = workbook.add_format({'bold': 1, 'align': 'top', 'valign': 'vcenter', 'text_wrap': 1})
            head = workbook.add_format({
                'bold': 1,
                'border': 0,
                'align': 'left',
                'valign': 'vcenter',
                'fg_color': 'white',
                'text_wrap': 1})
            head_boder = workbook.add_format({
                'bold': 1,
                'border': 1,
                'align': 'left',
                'valign': 'vcenter',
                'fg_color': 'white',
                'text_wrap': 1})
            title_format = workbook.add_format({
                'bold': 1,
                'border': 1,
                'font_size': 18,
                'align': 'center',
                'valign': 'vcenter',
                'text_wrap': 1,
                'fg_color': 'white'})
            user_login = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
            wssheet.merge_range('A2:D2', user_login.company_id.name, head)
            wssheet.merge_range('A3:D3', user_login.company_id.street, head)
            # wssheet.merge_range('A4:D4', user_login.company_id.phone + ' / ' + user_login.company_id.fax, head)

            wssheet.merge_range('A6:I8', u'PHIẾU YÊU CẦU', title_format)
            wssheet.write('A10', u'Mã phiếu', bold)

            wssheet.write('A11', u'Tên KH:', bold)
            wssheet.write('A12', u'Địa chỉ:', bold)
            wssheet.write('A13', u'Điện thoại:', bold)
            wssheet.write('F11', u'Biển số xe:', bold)
            wssheet.write('F12', u'Tên kiểu xe:', bold)
            wssheet.write('F13', u'Số khung:', bold)

            wssheet.write('B10', repair_id.sequence)
            wssheet.write('B11', repair_id.client_id.name)
            wssheet.write('B12', repair_id.client_id.street)
            wssheet.write('B13', repair_id.client_mobile + ('/' + repair_id.client_phone) if repair_id.client_phone else '')

            wssheet.write_row('A16', ['STT'], head_boder)
            wssheet.merge_range('B16:C16', u'Nội dung công việc', head_boder)
            wssheet.merge_range('D16:E16', u'SL vật tư & phụ tùng', head_boder)
            wssheet.merge_range('F16:G16', u'Thời gian thực hiện', head_boder)
            wssheet.merge_range('H16:I16', u'Nhân viên', head_boder)

            row = 16
            sale_order = self.env['sale.order'].search([('fleet_repair_id', '=', repair_id.id)])
            stt = 1
            # if sale_order:
            #     for sale_id in sale_order:
            #         so_line = self.env['sale.order.line'].search([('order_id', '=', sale_id.id)])
            #         repair_line = self.env['repair.order.line'].search([('order_id', '=', sale_id.id)])
            #         for order_line in so_line:
            #             row += 1
            #             wssheet.write('A' + str(row), [stt], bold_boder)
            #             wssheet.merge_range('B' + str(row) + ':' + 'D' + str(row), [order_line.name], bold_boder)
            #             wssheet.write('E' + str(row), [order_line.product_uom_qty], bold_boder)
            #             wssheet.write('F' + str(row), [order_line.product_uom_qty], bold_boder)
            #             wssheet.merge_range('G' + str(row) + ':' + 'H' + str(row), [repair_id.user_id.name], bold_boder)
            #             stt += 1

            row += 3
            wssheet.merge_range('B' + str(row) + ':' + 'C' + str(row), u'KHÁCH HÀNG', signature)
            wssheet.merge_range('D' + str(row) + ':' + 'E' + str(row), u'CỐ VẤN DỊCH VỤ', signature)
            wssheet.merge_range('F' + str(row) + ':' + 'G' + str(row), u'QUẢN ĐỐC', signature)
            wssheet.merge_range('H' + str(row) + ':' + 'I' + str(row), u'GIÁM ĐỐC', signature)

FleetRepairXlsx('report.car_repair_industry.fleet_repair_xlsx', 'fleet.repair')
