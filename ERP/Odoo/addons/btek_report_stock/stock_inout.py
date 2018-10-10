#!/usr/bin/python
# -*- encoding: utf-8 -*-
# ANHTT
from odoo import api, fields, models, _
import datetime, pytz
from odoo import tools


class StockLocation(models.Model):
    _inherit = 'stock.location'

    def _get_internal_sublocations(self, cr, uid, ids, context=None):
        """ return all internal sublocations of the given stock locations (included) """
        if context is None:
            context = {}

        return self.search(cr, uid, [('id', 'child_of', ids), ('usage', '=', 'internal')])


class NhapXuatKho(models.TransientModel):
    _name = 'stock.report.inout'

    @api.model
    def _gettoday(self):
        return datetime.date.today()

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    type = fields.Selection((('in', 'choose'), ('out', 'get')))
    lot_stock_id = fields.Many2one('stock.location', string="Location Stock", related='warehouse_id.lot_stock_id', required=True)
    start_date = fields.Date(default=_gettoday)
    end_date = fields.Date(default=_gettoday)

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    company_id = fields.Many2one('res.company', required=True, default=_get_company, string='Company')
    product_id = fields.Many2one('product.product',
                                 string="Product")
    product_category_id = fields.Many2one('product.category',
                                          string="Product Category")

    @api.multi
    def action_print(self):
        if self.type == 'in':
            return self.env['report'].get_action(self, 'btek_report_stock.stockin_report')
        else:
            return self.env['report'].get_action(self, 'btek_report_stock.stockout_report')


from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx


class Bangkephieunhap(ReportXlsx):
    _name = 'report.btek_report_stock.stockin_report'

    def write_data_inout(self, ws, data, form):
        ws.set_column(0, 0, 15)
        ws.set_column(1, 1, 15)
        ws.set_column(2, 2, 15)
        ws.set_column(3, 3, 30)
        ws.set_column(4, 4, 25)
        ws.set_column(5, 5, 28)
        ws.set_column(6, 6, 10)
        ws.set_column(7, 7, 15)
        ws.set_column(8, 8, 15)
        ws.set_column(9, 9, 15)
        ws.set_column(10, 10, 15)
        ws.set_column(11, 11, 15)
        ws.set_column(12, 12, 15)
        ws.set_column(13, 13, 15)
        ws.set_column(14, 14, 15)
        ws.set_row(7, 40)

        # Header
        address = u''
        if form.company_id.street: address = form.company_id.street
        if form.company_id.street2: address = address + ', ' + unicode(form.company_id.street2)
        if form.company_id.city: address = address + ', ' + unicode(form.company_id.city)
        ws.write('A%s' % 1, u'Đơn vị báo cáo:', )
        ws.merge_range('B1:E1', form.company_id.name, self.xxxxx)
        ws.write('A%s' % 2, u'Địa chỉ:', )
        ws.merge_range('B2:E2', address, self.xxxxx)
        if form.type == 'in':
            ws.merge_range('A4:J4', u'BẢNG KÊ PHIẾU NHẬP KHO HÀNG HÓA', self.title)
        else:
            ws.merge_range('A4:J4', u'BẢNG KÊ PHIẾU XUẤT KHO HÀNG HÓA', self.title)
        ws.merge_range('A6:J6', u'Từ ngày: ' + unicode(
            datetime.datetime.strptime(form.start_date, '%Y-%m-%d').strftime('%d/%m/%Y'))
                       + u' Đến ngày: ' + unicode(
            datetime.datetime.strptime(form.end_date, '%Y-%m-%d').strftime('%d/%m/%Y')), self.header)

        row = 8
        # ws.write('B%s' % row, u'Chọn', self.table_header)
        ws.merge_range('A8:B8', u'Chứng từ', self.table_header)
        ws.write('A%s' % 9, u'Mã chứng từ', self.table_header)
        ws.write('B%s' % 9, u'Ngày tháng', self.table_header)
        if form.type == 'in':
            ws.merge_range('C8:C9', u'Số phiếu nhập', self.table_header)
        else:
            ws.merge_range('C8:C9', u'Số phiếu xuất', self.table_header)
        ws.merge_range('D8:D9', u'Đối tượng', self.table_header)
        ws.merge_range('E8:E9', u'Mã hàng hóa', self.table_header)
        ws.merge_range('F8:F9', u'Tên hàng hóa', self.table_header)
        ws.merge_range('G8:G9', u'ĐVT', self.table_header)
        ws.merge_range('H8:H9', u'Số lượng', self.table_header)
        if form.type == 'in':
            ws.merge_range('I8:I9', u'Đơn giá nhập kho', self.table_header)
        else:
            ws.merge_range('I8:I9', u'Đơn giá xuất kho', self.table_header)
        ws.merge_range('J8:J9', u'Thành tiền', self.table_header)

        row = 10
        if data:
            sl = price_unit = price = 0
            for line in data:
                ws.write("A{row}".format(row=row), line['origin'] or '', self.table_row_left)
                ws.write("B{row}".format(row=row), line['date'] or '', self.table_row_left)
                ws.write("C{row}".format(row=row), line['reference'] or '', self.table_row_left)
                ws.write("D{row}".format(row=row), line['description_partner'] or '', self.table_row_left)
                ws.write("E{row}".format(row=row), line['product_code'] or '', self.table_row_left)
                ws.write("F{row}".format(row=row), line['product_name'] or '', self.table_row_left)
                ws.write("G{row}".format(row=row), line['product_uom'] or '', self.table_row_left)
                ws.write("H{row}".format(row=row), line['qty'] or 0, self.table_row_right)
                ws.write("I{row}".format(row=row), line['unit_price'] or 0, self.table_row_right)
                ws.write("J{row}".format(row=row), line['qty'] * line['unit_price'] or 0, self.table_row_right)

                sl = sl + (line['qty'] or 0)
                price_unit = price_unit + (line['unit_price'] or 0)
                price = price + (line['qty'] * line['unit_price'])
                row += 1

            ws.merge_range("A{row}:G{row}".format(row=row), u'Tổng cộng :', self.table_row_right_bold)
            ws.write("H{row}".format(row=row), sl or '', self.table_row_right_bold)
            ws.write("I{row}".format(row=row), price_unit or '', self.table_row_right_bold)
            ws.write("J{row}".format(row=row), price or '', self.table_row_right_bold)

            ws.merge_range("G{row}:J{row}".format(row=row + 2), u'Ngày ... tháng ... năm ...', self.center)
            ws.merge_range("G{row}:H{row}".format(row=row + 4), u'Người lập biểu', self.center_bold)
            ws.merge_range("I{row}:J{row}".format(row=row + 4), u'Kế toán trưởng', self.center_bold)
            ws.merge_range("G{row}:H{row}".format(row=row + 5), u'(Ký, họ tên)', self.center)
            ws.merge_range("I{row}:J{row}".format(row=row + 5), u'(Ký, họ tên)', self.center)

        if form.type == 'out':
            self.title = unicode("Bang_ke_phieu_xuat_tu_{start}_den_ {end}").format(
                start=unicode(datetime.datetime.strptime(form.start_date, '%Y-%m-%d').strftime('%d/%m/%Y')),
                end=unicode(datetime.datetime.strptime(form.start_date, '%Y-%m-%d').strftime('%d/%m/%Y')))

        else:
            self.title = unicode("Bang_ke_phieu_nhap_tu_{start}_den_ {end}").format(
                start=unicode(datetime.datetime.strptime(form.start_date, '%Y-%m-%d').strftime('%d/%m/%Y')),
                end=unicode(datetime.datetime.strptime(form.start_date, '%Y-%m-%d').strftime('%d/%m/%Y')))

    def generate_xlsx_report(self, wb, data, form):
        reports = {
            'report': self.write_data_inout,
        }
        # ws = wb.add_worksheet('report')
        if form.type == 'out':
            ws = wb.add_worksheet(unicode("Bang_ke_phieu_xuat_tu_{start}_den_ {end}").format(
                start=unicode(datetime.datetime.strptime(form.start_date, '%Y-%m-%d').strftime('%d/%m/%Y')),
                end=unicode(datetime.datetime.strptime(form.start_date, '%Y-%m-%d').strftime('%d/%m/%Y')))
                                  )
            self.title = unicode("Bang_ke_phieu_xuat_tu_{start}_den_ {end}").format(
                start=unicode(datetime.datetime.strptime(form.start_date, '%Y-%m-%d').strftime('%d/%m/%Y')),
                end=unicode(datetime.datetime.strptime(form.start_date, '%Y-%m-%d').strftime('%d/%m/%Y')))

        else:
            ws = wb.add_worksheet(unicode("Bang_ke_phieu_nhap_tu_{start}_den_ {end}").format(
                start=unicode(datetime.datetime.strptime(form.start_date, '%Y-%m-%d').strftime('%d/%m/%Y')),
                end=unicode(datetime.datetime.strptime(form.start_date, '%Y-%m-%d').strftime('%d/%m/%Y')))
            )
            self.title = unicode("Bang_ke_phieu_nhap_tu_{start}_den_ {end}").format(
                start=unicode(datetime.datetime.strptime(form.start_date, '%Y-%m-%d').strftime('%d/%m/%Y')),
                end=unicode(datetime.datetime.strptime(form.start_date, '%Y-%m-%d').strftime('%d/%m/%Y')))
        wb.formats[0].font_name = 'Times New Roman'
        wb.formats[0].font_size = 11
        ws.set_paper(9)
        ws.center_horizontally()
        ws.set_margins(left=0.28, right=0.28, top=0.5, bottom=0.5)
        ws.fit_to_pages(1, 0)
        ws.set_landscape()
        ws.fit_to_pages(1, 1)

        # DEFINE FORMATS
        self.header = wb.add_format({
            'bold': 1,
            'text_wrap': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_name': 'Times New Roman'
        })

        self.xxxxx = wb.add_format({
            'bold': 1,
            'text_wrap': 1,
            'font_name': 'Times New Roman'
        })
        self.title = wb.add_format({
            'bold': 1,
            'text_wrap': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 15,
            'font_name': 'Times New Roman',
        })
        self.bold_right_big = wb.add_format({
            'bold': 1,
            'text_wrap': 1,
            'align': 'right',
            'valign': 'vcenter',
            'font_name': 'Times New Roman'
        })
        self.bold = wb.add_format({
            'bold': 1,
            'text_wrap': 1,
            'valign': 'vcenter',
            'font_name': 'Times New Roman'
        })
        self.right = wb.add_format({
            'text_wrap': 1,
            'align': 'right',
            'valign': 'vcenter',
            'num_format': '#,##0.00',
            'font_name': 'Times New Roman'
        })

        self.center = wb.add_format({
            'text_wrap': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_name': 'Times New Roman'
        })

        self.center_bold = wb.add_format({
            'text_wrap': 1,
            'align': 'center',
            'valign': 'vcenter',
            'bold': 1,
            'font_name': 'Times New Roman'
        })
        self.table_header = wb.add_format({
            'bold': 1,
            'text_wrap': 1,
            'align': 'center',
            'valign': 'vcenter',
            # 'bg_color': '#C6EFCE',
            'border': 1,
            'font_name': 'Times New Roman',
        })

        self.table_row_left = wb.add_format({
            'text_wrap': 1,
            'align': 'left',
            'valign': 'vcenter',
            'border': 1,
            'font_name': 'Times New Roman',
        })

        self.table_row_left_bold = wb.add_format({
            'text_wrap': 1,
            'align': 'left',
            'bold': 1,
            'valign': 'vcenter',
            'border': 1,
            'font_name': 'Times New Roman',
        })

        self.table_row_right = wb.add_format({
            'text_wrap': 1,
            'align': 'right',
            'valign': 'vcenter',
            'border': 1,
            'num_format': '#,##0.00',
            'font_name': 'Times New Roman',
        })
        self.table_row_right_bold = wb.add_format({
            'text_wrap': 1,
            'align': 'right',
            'valign': 'vcenter',
            'bold': 1,
            'border': 1,
            'num_format': '#,##0.00',
            'font_name': 'Times New Roman',
        })

        args = {
            'date_from': form.start_date,
            'date_to': form.end_date,
            'lot_stock_id': form.lot_stock_id or False,
            'product': form.product_id or False,
            'product_category': form.product_category_id or False,
            'type': form.type,
            'warehouse_id': form.warehouse_id or False
        }
        report_data = self.get_data_from_query(args)
        reports['report'](ws, report_data, form)

    def get_data_from_query(self, kwargs):
        sql = self.get_query(kwargs)
        self.env.cr.execute(sql)
        data = self.env.cr.dictfetchall()
        return data

    def get_query(self, kwargs):
        date_from = kwargs['date_from']
        date_to = kwargs['date_to']
        location_ids = 'NULL'
        if kwargs['lot_stock_id'] is not False:
            location_id = kwargs['lot_stock_id'].id
            location = self.env['stock.location'].browse(location_id).location_id
            location_ids = ','.join(str(x) for x in self.env['stock.location'].search(
                [('id', 'child_of', location_id), ('usage', '=', 'internal')]).ids)
        filter_product = '-- no filter product'
        if kwargs['product']:
            product_id = kwargs['product'].id
            filter_product = """AND p.id ={product_id}""".format(product_id=product_id)
        filter_categories = '-- no filter categories'
        if kwargs['product_category']:
            product_cate_id = kwargs['product_category'].id
            category = self.env['product.category'].browse(product_cate_id)
            product_cate_ids = ','.join(
                str(x) for x in self.env['product.category'].search([('id', 'child_of', product_cate_id)]).ids)
            filter_categories = """AND tmpl.categ_id in ({product_cate_ids})""".format(
                product_cate_ids=product_cate_ids)
            if len(self.env['product.category'].search([('id', 'child_of', product_cate_id)]).ids) == 0:
                filter_categories = '-- no filter categories'
        if kwargs['type'] == 'in':
            inout_type = '> 0'
        else:
            inout_type = '< 0'
        res_company_id = self.env.user.company_id.id
        sql = """
                SELECT
                CASE WHEN sm.picking_id is not null THEN sp.origin ELSE null END AS origin,
                CASE WHEN sm.picking_id is not null THEN sp.name ELSE
                (CASE WHEN sm.inventory_id is not null THEN si.name ELSE null END) END AS reference,
                src_loc.name AS src_loc_name,
                dest_loc.name AS dest_loc_name,
                to_char(sh.date,'dd/mm/yyyy') AS date,
                sh.price_unit_on_quant AS unit_price,
                
                SUM(ABS(sh.quantity)) AS qty,
                sp.note,
                sm.name AS description,
                
                tmpl.name AS product_name,
                p.default_code AS product_code,
                uom.name AS product_uom,
                
                rp.name as description_partner
            FROM stock_history AS sh

                INNER JOIN stock_move AS sm ON sm.id = sh.move_id
                LEFT JOIN stock_picking AS sp ON sp.id = sm.picking_id
                LEFT JOIN stock_inventory AS si ON si.id = sm.inventory_id
                LEFT JOIN res_partner rp on rp.id = sp.partner_id
                INNER JOIN product_product AS p ON p.id =  sh.product_id
                LEFT JOIN product_template AS tmpl ON tmpl.id = p.product_tmpl_id
                LEFT JOIN product_uom AS uom ON uom.id = tmpl.uom_id
                
                INNER JOIN stock_location AS loc ON loc.id = sh.location_id
                INNER JOIN stock_location AS src_loc ON src_loc.id = sm.location_id
                INNER JOIN stock_location AS dest_loc ON dest_loc.id = sm.location_dest_id
            WHERE sh.date::date >= '{date_from}' AND sh.date::date <= '{date_to}' AND
            ((src_loc.company_id is null AND dest_loc.company_id is not null) OR
                        (src_loc.company_id is not null AND dest_loc.company_id is null) OR
                        src_loc.company_id != dest_loc.company_id OR
                        src_loc.usage not in ('internal', 'transit') OR
                        --(dest_loc.usage not in ('transit')  AND dest_loc.is_agency_location = true) OR
                        (dest_loc.usage not in ('transit')
                             AND dest_loc.company_id = src_loc.company_id
                             AND REPLACE(SUBSTRING(dest_loc.complete_name, '/(( )*\w*( )*)'),' ','') != REPLACE(SUBSTRING(src_loc.complete_name, '/(( )*\w*( )*)'),' ','')
                            )
                        )
                    AND sh.company_id = {res_company_id} AND sh.quantity """ + inout_type + """
                    """ + filter_product + """
                """ + filter_categories + """
                AND  CASE WHEN '{location_ids}' = 'NULL'  THEN 1=1 ELSE loc.id in ({location_ids}) END  --loc.id in {location_ids}
                
                GROUP BY sp.name, si.name, sm.picking_id, sm.inventory_id,
                sp.origin, sh.date,sh.price_unit_on_quant,product_name,p.default_code,uom.name,rp.name,
                src_loc.name,dest_loc.name,sp.note,sm.name
            ORDER BY sh.date ASC
        """
        x_location_ids = 'NULL' if location_ids == 'NULL' else (location_ids)
        sql = sql.format(date_from=date_from, date_to=date_to, res_company_id=res_company_id,
                         location_ids=x_location_ids)
        return sql


Bangkephieunhap('report.btek_report_stock.stockin_report', 'stock.report.inout')

from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx


class Bangkephieuxuat(ReportXlsx):
    _name = 'report.btek_report_stock.stockout_report'

    def change_utc_to_local_datetime(self, souce_date):
        user_tz = self.env.user.tz or str(pytz.utc)
        tz_now = datetime.datetime.now(pytz.timezone(user_tz))
        difference = tz_now.utcoffset().total_seconds() / 60 / 60
        difference = int(difference)
        utc_date = datetime.datetime.strptime(souce_date,
                                              '%Y-%m-%d %H:%M:%S')
        local_date = utc_date + datetime.timedelta(hours=difference)

        return local_date.strftime('%d/%m/%Y')

    def change_local_datetime_to_utc(self, souce_date):
        user_tz = self.env.user.tz or str(pytz.utc)
        tz_now = datetime.datetime.now(pytz.timezone(user_tz))
        difference = tz_now.utcoffset().total_seconds() / 60 / 60
        difference = int(difference)
        local_date = datetime.datetime.strptime(souce_date,
                                              '%Y-%m-%d %H:%M:%S')
        utc_date = local_date + datetime.timedelta(hours=-difference)

        return utc_date.strftime('%Y-%m-%d %H:%M:%S')

    def write_data_inout(self, ws, data, form):
        ws.set_column(0, 0, 15)
        ws.set_column(1, 1, 15)
        ws.set_column(2, 2, 15)
        ws.set_column(3, 3, 30)
        ws.set_column(4, 4, 25)
        ws.set_column(5, 5, 28)
        ws.set_column(6, 6, 10)
        ws.set_column(7, 7, 15)
        ws.set_column(8, 8, 15)
        ws.set_column(9, 9, 15)
        ws.set_column(10, 10, 15)
        ws.set_column(11, 11, 15)
        ws.set_column(12, 12, 15)
        ws.set_column(13, 13, 15)
        ws.set_column(14, 14, 15)
        ws.set_row(7, 40)

        # Header
        address = u''
        if form.company_id.street: address = form.company_id.street
        if form.company_id.street2: address = address + ', ' + unicode(form.company_id.street2)
        if form.company_id.city: address = address + ', ' + unicode(form.company_id.city)
        ws.write('A%s' % 1, u'Đơn vị báo cáo:', )
        ws.merge_range('B1:E1', form.company_id.name, self.xxxxx)
        ws.write('A%s' % 2, u'Địa chỉ:', )
        ws.merge_range('B2:E2', address, self.xxxxx)
        if form.type == 'in':
            ws.merge_range('A4:J4', u'BẢNG KÊ PHIẾU NHẬP KHO HÀNG HÓA', self.title)
        else:
            ws.merge_range('A4:J4', u'BẢNG KÊ PHIẾU XUẤT KHO HÀNG HÓA', self.title)
        ws.merge_range('A6:J6', u'Từ ngày: ' + unicode(
            datetime.datetime.strptime(form.start_date, '%Y-%m-%d').strftime('%d/%m/%Y'))
                       + u' Đến ngày: ' + unicode(
            datetime.datetime.strptime(form.end_date, '%Y-%m-%d').strftime('%d/%m/%Y')), self.header)

        row = 8
        # ws.write('B%s' % row, u'Chọn', self.table_header)
        ws.merge_range('A8:B8', u'Chứng từ', self.table_header)
        ws.write('A%s' % 9, u'Mã chứng từ', self.table_header)
        ws.write('B%s' % 9, u'Ngày tháng', self.table_header)
        if form.type == 'in':
            ws.merge_range('C8:C9', u'Số phiếu nhập', self.table_header)
        else:
            ws.merge_range('C8:C9', u'Số phiếu xuất', self.table_header)
        ws.merge_range('D8:D9', u'Đối tượng', self.table_header)
        ws.merge_range('E8:E9', u'Mã hàng hóa', self.table_header)
        ws.merge_range('F8:F9', u'Tên hàng hóa', self.table_header)
        ws.merge_range('G8:G9', u'ĐVT', self.table_header)
        ws.merge_range('H8:H9', u'Số lượng', self.table_header)
        if form.type == 'in':
            ws.merge_range('I8:I9', u'Đơn giá nhập kho', self.table_header)
        else:
            ws.merge_range('I8:I9', u'Đơn giá xuất kho', self.table_header)
        ws.merge_range('J8:J9', u'Thành tiền', self.table_header)

        row = 10
        if data:
            sl = price_unit = price = 0
            for line in data:
                ws.write("A{row}".format(row=row), line['origin'] or '', self.table_row_left)
                ws.write("B{row}".format(row=row), line['date'] and self.change_utc_to_local_datetime(line['date']) or '', self.table_row_left)
                ws.write("C{row}".format(row=row), line['reference'] or '', self.table_row_left)
                ws.write("D{row}".format(row=row), line['description_partner'] or '', self.table_row_left)
                ws.write("E{row}".format(row=row), line['product_code'] or '', self.table_row_left)
                ws.write("F{row}".format(row=row), line['product_name'] or '', self.table_row_left)
                ws.write("G{row}".format(row=row), line['product_uom'] or '', self.table_row_left)
                ws.write("H{row}".format(row=row), line['qty'] or 0, self.table_row_right)
                ws.write("I{row}".format(row=row), line['unit_price'] or 0, self.table_row_right)
                ws.write("J{row}".format(row=row), line['qty'] * line['unit_price'] or 0, self.table_row_right)

                sl = sl + (line['qty'] or 0)
                price_unit = price_unit + (line['unit_price'] or 0)
                price = price + (line['qty'] * line['unit_price'])
                row += 1

            ws.merge_range("A{row}:G{row}".format(row=row), u'Tổng cộng :', self.table_row_right_bold)
            ws.write("H{row}".format(row=row), sl or '', self.table_row_right_bold)
            ws.write("I{row}".format(row=row), price_unit or '', self.table_row_right_bold)
            ws.write("J{row}".format(row=row), price or '', self.table_row_right_bold)

            ws.merge_range("G{row}:J{row}".format(row=row + 2), u'Ngày ... tháng ... năm ...', self.center)
            ws.merge_range("G{row}:H{row}".format(row=row + 4), u'Người lập biểu', self.center_bold)
            ws.merge_range("I{row}:J{row}".format(row=row + 4), u'Kế toán trưởng', self.center_bold)
            ws.merge_range("G{row}:H{row}".format(row=row + 5), u'(Ký, họ tên)', self.center)
            ws.merge_range("I{row}:J{row}".format(row=row + 5), u'(Ký, họ tên)', self.center)

        if form.type == 'out':
            self.title = unicode("Bang_ke_phieu_xuat_tu_{start}_den_ {end}").format(
                start=unicode(datetime.datetime.strptime(form.start_date, '%Y-%m-%d').strftime('%d/%m/%Y')),
                end=unicode(datetime.datetime.strptime(form.start_date, '%Y-%m-%d').strftime('%d/%m/%Y')))

        else:
            self.title = unicode("Bang_ke_phieu_nhap_tu_{start}_den_ {end}").format(
                start=unicode(datetime.datetime.strptime(form.start_date, '%Y-%m-%d').strftime('%d/%m/%Y')),
                end=unicode(datetime.datetime.strptime(form.start_date, '%Y-%m-%d').strftime('%d/%m/%Y')))

    def generate_xlsx_report(self, wb, data, form):
        reports = {
            'report': self.write_data_inout,
        }
        # ws = wb.add_worksheet('report')
        if form.type == 'out':
            ws = wb.add_worksheet(unicode("Bang_ke_phieu_xuat_tu_{start}_den_ {end}").format(
                start=unicode(datetime.datetime.strptime(form.start_date, '%Y-%m-%d').strftime('%d/%m/%Y')),
                end=unicode(datetime.datetime.strptime(form.start_date, '%Y-%m-%d').strftime('%d/%m/%Y')))
                                  )
            self.title = unicode("Bang_ke_phieu_xuat_tu_{start}_den_ {end}").format(
                start=unicode(datetime.datetime.strptime(form.start_date, '%Y-%m-%d').strftime('%d/%m/%Y')),
                end=unicode(datetime.datetime.strptime(form.start_date, '%Y-%m-%d').strftime('%d/%m/%Y')))

        else:
            ws = wb.add_worksheet(unicode("Bang_ke_phieu_nhap_tu_{start}_den_ {end}").format(
                start=unicode(datetime.datetime.strptime(form.start_date, '%Y-%m-%d').strftime('%d/%m/%Y')),
                end=unicode(datetime.datetime.strptime(form.start_date, '%Y-%m-%d').strftime('%d/%m/%Y')))
            )
            self.title = unicode("Bang_ke_phieu_nhap_tu_{start}_den_ {end}").format(
                start=unicode(datetime.datetime.strptime(form.start_date, '%Y-%m-%d').strftime('%d/%m/%Y')),
                end=unicode(datetime.datetime.strptime(form.start_date, '%Y-%m-%d').strftime('%d/%m/%Y')))
        wb.formats[0].font_name = 'Times New Roman'
        wb.formats[0].font_size = 11
        ws.set_paper(9)
        ws.center_horizontally()
        ws.set_margins(left=0.28, right=0.28, top=0.5, bottom=0.5)
        ws.fit_to_pages(1, 0)
        ws.set_landscape()
        ws.fit_to_pages(1, 1)

        # DEFINE FORMATS
        self.header = wb.add_format({
            'bold': 1,
            'text_wrap': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_name': 'Times New Roman'
        })

        self.xxxxx = wb.add_format({
            'bold': 1,
            'text_wrap': 1,
            'font_name': 'Times New Roman'
        })
        self.title = wb.add_format({
            'bold': 1,
            'text_wrap': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 15,
            'font_name': 'Times New Roman',
        })
        self.bold_right_big = wb.add_format({
            'bold': 1,
            'text_wrap': 1,
            'align': 'right',
            'valign': 'vcenter',
            'font_name': 'Times New Roman'
        })
        self.bold = wb.add_format({
            'bold': 1,
            'text_wrap': 1,
            'valign': 'vcenter',
            'font_name': 'Times New Roman'
        })
        self.right = wb.add_format({
            'text_wrap': 1,
            'align': 'right',
            'valign': 'vcenter',
            'num_format': '#,##0.00',
            'font_name': 'Times New Roman'
        })

        self.center = wb.add_format({
            'text_wrap': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_name': 'Times New Roman'
        })

        self.center_bold = wb.add_format({
            'text_wrap': 1,
            'align': 'center',
            'valign': 'vcenter',
            'bold': 1,
            'font_name': 'Times New Roman'
        })
        self.table_header = wb.add_format({
            'bold': 1,
            'text_wrap': 1,
            'align': 'center',
            'valign': 'vcenter',
            # 'bg_color': '#C6EFCE',
            'border': 1,
            'font_name': 'Times New Roman',
        })

        self.table_row_left = wb.add_format({
            'text_wrap': 1,
            'align': 'left',
            'valign': 'vcenter',
            'border': 1,
            'font_name': 'Times New Roman',
        })

        self.table_row_left_bold = wb.add_format({
            'text_wrap': 1,
            'align': 'left',
            'bold': 1,
            'valign': 'vcenter',
            'border': 1,
            'font_name': 'Times New Roman',
        })

        self.table_row_right = wb.add_format({
            'text_wrap': 1,
            'align': 'right',
            'valign': 'vcenter',
            'border': 1,
            'num_format': '#,##0.00',
            'font_name': 'Times New Roman',
        })
        self.table_row_right_bold = wb.add_format({
            'text_wrap': 1,
            'align': 'right',
            'valign': 'vcenter',
            'bold': 1,
            'border': 1,
            'num_format': '#,##0.00',
            'font_name': 'Times New Roman',
        })

        args = {
            'date_from': form.start_date,
            'date_to': form.end_date,
            'lot_stock_id': form.lot_stock_id or False,
            'product': form.product_id or False,
            'product_category': form.product_category_id or False,
            'type': form.type,
            'warehouse_id': form.warehouse_id or False,
            'company_id': form.company_id
        }
        report_data = self.get_data_from_query(args)
        reports['report'](ws, report_data, form)

    def get_data_from_query(self, kwargs):
        sql = self.get_query(kwargs)
        self.env.cr.execute(sql)
        data = self.env.cr.dictfetchall()
        return data

    def get_query(self, kwargs):
        where_clause = ''
        date_from = kwargs['date_from']
        if date_from:
            date_from = date_from + ' 00:00:00'
            date_from = self.change_local_datetime_to_utc(date_from)
            where_clause = "{} and sp.date_done >= '{}'".format(
                where_clause, date_from)
        date_to = kwargs['date_to']
        if date_to:
            date_to = date_to + ' 23:59:59'
            date_to = self.change_local_datetime_to_utc(date_to)
            where_clause = "{} and sp.date_done <= '{}'".format(
                where_clause, date_to)
        
        if kwargs['lot_stock_id'] is not False:
            location_id = kwargs['lot_stock_id'].id
            location_ids = ','.join(str(x) for x in self.env['stock.location'].search(
                [('id', 'child_of', location_id), ('usage', '=', 'internal')]).ids)
            where_clause = '{} and src_loc.id in ({})'.format(
                where_clause, location_ids)

        if kwargs['product']:
            product_id = kwargs['product'].id
            where_clause = '{} and pp.id = {}'.format(
                where_clause, product_id)

        if kwargs['product_category']:
            product_cate_id = kwargs['product_category'].id
            product_cate_ids = ','.join(
                str(x) for x in self.env['product.category'].search(
                    [('id', 'child_of', product_cate_id)]).ids)
            where_clause = '{} and pt.categ_id in ({})'.format(
                product_cate_ids)

        res_company_id = kwargs['company_id'].id
        where_clause = '{} and sp.company_id = {}'.format(
            where_clause, res_company_id
        )

        sql = """
                select sm.id as smid,
                    sm.name as description,
                    sp.origin, sp.date_done as date,
                    sp.name as reference,
                    pp.default_code as product_code,
                    src_loc.name AS src_loc_name,
                    dest_loc.name AS dest_loc_name,
                    pt.name as product_name,
                    aml.product_uom_id,
                    aml.quantity as qty,
                    sp.note,
                    uom.name as product_uom,
                    rp.name as description_partner,
                    abs(sm.price_unit) as unit_price,
                    abs(aml.debit-aml.credit) as balance
                from stock_move as sm
                left join stock_picking as sp on sp.id = sm.picking_id
                left join account_move_line as aml on sm.id = aml.x_stock_move_id
                left join account_move as am on am.id = aml.move_id
                left join product_product as pp on pp.id = sm.product_id
                left join product_template as pt on pt.id = pp.product_tmpl_id
                left join stock_picking_type as spt on spt.id = sp.picking_type_id
                left join stock_location as src_loc on src_loc.id = sm.location_id
                left join stock_location as dest_loc on src_loc.id = sm.location_dest_id
                left join product_uom as uom on sm.product_uom = uom.id
                left join res_partner rp on rp.id = sp.partner_id
                where spt.code = 'outgoing'
                 and aml.debit > aml.credit
                {}
        """.format(where_clause)
        return sql

Bangkephieuxuat('report.btek_report_stock.stockout_report', 'stock.report.inout')
