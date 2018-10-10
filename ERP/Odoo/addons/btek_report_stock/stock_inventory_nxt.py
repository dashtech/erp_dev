#!/usr/bin/python
# -*- encoding: utf-8 -*-
# ANHTT
from odoo import api, fields, models, _
import datetime
from datetime import timedelta
from odoo import tools
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class StockInventoryNxt(models.TransientModel):
    _name = 'stock.inventory.nxt'

    @api.model_cr
    def init(self):
        from odoo import tools
        tools.drop_view_if_exists(self.env.cr, 's11_view')
        self.env.cr.execute("""
                CREATE OR REPLACE VIEW public.s11_view AS 
                    SELECT product_product.default_code AS code,
                    product_template.name AS name,
                    dest_location.id AS location_id,
                    stock_move.company_id,
                        CASE
                            WHEN source_location.usage::text <> 'internal'::text AND dest_location.usage::text = 'internal'::text THEN false
                            WHEN source_location.usage::text = 'internal'::text AND dest_location.usage::text = 'internal'::text THEN false
                            WHEN dest_location.usage::text = 'internal'::text AND source_location.usage::text = 'internal'::text AND replace("substring"(dest_location.complete_name::text, '/(( )*\w*( )*)'::text), ' '::text, ''::text) <> replace("substring"(source_location.complete_name::text, '/(( )*\w*( )*)'::text), ' '::text, ''::text) THEN true
                            WHEN ir.value_text = 'real_time'::text THEN NULL::boolean
                            ELSE NULL::boolean
                        END AS kieu,
                        CASE
                            WHEN ir.value_text = 'real_time'::text AND source_location.usage::text <> 'internal'::text AND dest_location.usage::text = 'internal'::text THEN sm_acc_line.quantity
                            WHEN ir.value_text = 'real_time'::text AND source_location.usage::text = 'internal'::text AND dest_location.usage::text = 'internal'::text  THEN sm_acc_line.quantity
                            WHEN ir.value_text = 'real_time'::text AND dest_location.usage::text = 'internal'::text AND source_location.usage::text = 'internal'::text AND replace("substring"(dest_location.complete_name::text, '/(( )*\w*( )*)'::text), ' '::text, ''::text) <> replace("substring"(source_location.complete_name::text, '/(( )*\w*( )*)'::text), ' '::text, ''::text) THEN stock_move.product_qty
                            WHEN ir.value_text = 'real_time'::text THEN NULL::numeric
                            ELSE stock_move.product_qty
                        END AS quantity,
                        CASE
                            WHEN ir.value_text = 'real_time'::text AND source_location.usage::text <> 'internal'::text AND dest_location.usage::text = 'internal'::text THEN sm_acc_line.price_unit::double precision
                            WHEN ir.value_text = 'real_time'::text AND source_location.usage::text = 'internal'::text AND dest_location.usage::text = 'internal'::text  THEN sm_acc_line.price_unit::double precision
                            WHEN ir.value_text = 'real_time'::text AND dest_location.usage::text = 'internal'::text AND source_location.usage::text = 'internal'::text AND replace("substring"(dest_location.complete_name::text, '/(( )*\w*( )*)'::text), ' '::text, ''::text) <> replace("substring"(source_location.complete_name::text, '/(( )*\w*( )*)'::text), ' '::text, ''::text) THEN stock_move.price_unit
                            WHEN ir.value_text = 'real_time'::text THEN NULL::double precision
                            ELSE stock_move.price_unit
                        END AS price_unit_on_quant,
                        CASE
                            WHEN source_location.usage::text <> 'internal'::text AND dest_location.usage::text = 'internal'::text THEN sm_acc_line.account_id
                            WHEN source_location.usage::text = 'internal'::text AND dest_location.usage::text = 'internal'::text  THEN sm_acc_line.account_id
                            --WHEN dest_location.usage::text = 'internal'::text AND source_location.usage::text = 'internal'::text AND replace("substring"(dest_location.complete_name::text, '/(( )*\w*( )*)'::text), ' '::text, ''::text) <> replace("substring"(source_location.complete_name::text, '/(( )*\w*( )*)'::text), ' '::text, ''::text) THEN
                            --CASE
                            --    WHEN ir_category.value_reference IS NOT NULL THEN "substring"(ir_category.value_reference::text, 17)::integer
                            --    WHEN ir_product.value_reference IS NOT NULL THEN "substring"(ir_product.value_reference::text, 17)::integer
                            --    ELSE NULL::integer
                            --END
                            ELSE NULL::integer
                        END AS account_id,
                        CASE
                            WHEN stock_move.picking_id IS NOT NULL THEN stock_picking.date_done
                            WHEN stock_move.inventory_id IS NOT NULL THEN stock_inventory.date
                            ELSE stock_move.date
                        END AS date,
                    stock_move.product_qty AS quantity_stock_move,
                    stock_move.price_unit AS price_unit_stock_move,
                    sm_acc_line.debit AS total_amount
                    FROM stock_move
                     JOIN stock_location dest_location ON stock_move.location_dest_id = dest_location.id
                     JOIN stock_location source_location ON stock_move.location_id = source_location.id
                     JOIN product_product ON product_product.id = stock_move.product_id
                     JOIN product_template ON product_template.id = product_product.product_tmpl_id
                     LEFT JOIN stock_picking ON stock_move.picking_id = stock_picking.id
                     LEFT JOIN stock_inventory ON stock_inventory.id = stock_move.inventory_id
                     LEFT JOIN stock_picking_type spt ON spt.id = stock_move.picking_type_id
                     LEFT JOIN stock_move_account_move_line_rel_view sm_acc_line ON sm_acc_line.stock_move_id = stock_move.id AND sm_acc_line.location_id = stock_move.location_dest_id
                     LEFT JOIN ir_property ir ON "substring"(ir.res_id::text, 18)::integer = product_template.id AND ir.name::text = 'valuation'::text AND ir.company_id = stock_move.company_id
                     LEFT JOIN ir_property ir_product ON "substring"(ir_product.res_id::text, 18)::integer = product_template.id AND ir_product.name::text = 'property_stock_valuation_account_id'::text AND ir_product.company_id = stock_move.company_id
                     LEFT JOIN ir_property ir_category ON "substring"(ir_category.res_id::text, 18)::integer = product_template.categ_id AND ir_category.name::text = 'property_stock_valuation_account_id'::text AND ir_category.company_id = stock_move.company_id
                    WHERE stock_move.state::text = 'done'::text AND dest_location.usage::text = 'internal'::text AND product_template.type::text = 'product'::text AND (source_location.usage::text <> 'internal'::text OR source_location.usage::text = 'internal'::text AND (replace("substring"(dest_location.complete_name::text, '/(( )*\w*( )*)'::text), ' '::text, ''::text) <> replace("substring"(source_location.complete_name::text, '/(( )*\w*( )*)'::text), ' '::text, ''::text)))
                    UNION ALL
                    SELECT product_product.default_code AS code,
                    product_template.name AS name,
                    source_location.id AS location_id,
                    stock_move.company_id,
                        CASE
                            WHEN source_location.usage::text = 'internal'::text AND dest_location.usage::text <> 'internal'::text THEN false
                            WHEN source_location.usage::text = 'internal'::text AND dest_location.usage::text = 'internal'::text  THEN false
                            WHEN dest_location.usage::text = 'internal'::text AND source_location.usage::text = 'internal'::text AND replace("substring"(dest_location.complete_name::text, '/(( )*\w*( )*)'::text), ' '::text, ''::text) <> replace("substring"(source_location.complete_name::text, '/(( )*\w*( )*)'::text), ' '::text, ''::text) THEN true
                            WHEN ir.value_text = 'real_time'::text THEN NULL::boolean
                            ELSE NULL::boolean
                        END AS kieu,
                        CASE
                            WHEN ir.value_text = 'real_time'::text AND source_location.usage::text = 'internal'::text AND dest_location.usage::text <> 'internal'::text THEN - sm_acc_line.quantity
                            WHEN ir.value_text = 'real_time'::text AND source_location.usage::text = 'internal'::text AND dest_location.usage::text = 'internal'::text  THEN - sm_acc_line.quantity
                            WHEN ir.value_text = 'real_time'::text AND dest_location.usage::text = 'internal'::text AND source_location.usage::text = 'internal'::text AND replace("substring"(dest_location.complete_name::text, '/(( )*\w*( )*)'::text), ' '::text, ''::text) <> replace("substring"(source_location.complete_name::text, '/(( )*\w*( )*)'::text), ' '::text, ''::text) THEN - stock_move.product_qty
                            WHEN ir.value_text = 'real_time'::text THEN NULL::numeric
                            ELSE - stock_move.product_qty
                        END AS quantity,
                        CASE
                            WHEN ir.value_text = 'real_time'::text AND source_location.usage::text = 'internal'::text AND dest_location.usage::text <> 'internal'::text THEN - sm_acc_line.price_unit::double precision
                            WHEN ir.value_text = 'real_time'::text AND source_location.usage::text = 'internal'::text AND dest_location.usage::text = 'internal'::text THEN - sm_acc_line.price_unit::double precision
                            WHEN ir.value_text = 'real_time'::text AND dest_location.usage::text = 'internal'::text AND source_location.usage::text = 'internal'::text AND replace("substring"(dest_location.complete_name::text, '/(( )*\w*( )*)'::text), ' '::text, ''::text) <> replace("substring"(source_location.complete_name::text, '/(( )*\w*( )*)'::text), ' '::text, ''::text) THEN - stock_move.price_unit
                            WHEN ir.value_text = 'real_time'::text THEN NULL::double precision
                            ELSE - stock_move.price_unit
                        END AS price_unit_on_quant,
                        CASE
                            WHEN source_location.usage::text = 'internal'::text AND dest_location.usage::text <> 'internal'::text THEN sm_acc_line.account_id
                            WHEN source_location.usage::text = 'internal'::text AND dest_location.usage::text = 'internal'::text  THEN sm_acc_line.account_id
                            --WHEN ir.value_text = 'real_time'::text AND dest_location.usage::text = 'internal'::text AND source_location.usage::text = 'internal'::text AND replace("substring"(dest_location.complete_name::text, '/(( )*\w*( )*)'::text), ' '::text, ''::text) <> replace("substring"(source_location.complete_name::text, '/(( )*\w*( )*)'::text), ' '::text, ''::text) THEN
                            --CASE
                            --    WHEN ir_category.value_reference IS NOT NULL THEN "substring"(ir_category.value_reference::text, 17)::integer
                            --    WHEN ir_product.value_reference IS NOT NULL THEN "substring"(ir_product.value_reference::text, 17)::integer
                            --    ELSE NULL::integer
                            --END
                            ELSE NULL::integer
                        END AS account_id,
                        CASE
                            WHEN stock_move.picking_id IS NOT NULL THEN stock_picking.date_done
                            WHEN stock_move.inventory_id IS NOT NULL THEN stock_inventory.date
                            ELSE stock_move.date
                        END AS date,
                    - stock_move.product_qty AS quantity_stock_move,
                    - stock_move.price_unit AS price_unit_stock_move,
                    - sm_acc_line.credit AS total_amount
                    FROM stock_move
                     JOIN stock_location source_location ON stock_move.location_id = source_location.id
                     JOIN stock_location dest_location ON stock_move.location_dest_id = dest_location.id
                     JOIN product_product ON product_product.id = stock_move.product_id
                     JOIN product_template ON product_template.id = product_product.product_tmpl_id
                     LEFT JOIN stock_picking ON stock_move.picking_id = stock_picking.id
                     LEFT JOIN stock_picking_type spt ON spt.id = stock_move.picking_type_id
                     LEFT JOIN stock_inventory ON stock_inventory.id = stock_move.inventory_id
                     LEFT JOIN stock_move_account_move_line_rel_view sm_acc_line ON sm_acc_line.stock_move_id = stock_move.id AND sm_acc_line.location_id = stock_move.location_id
                     LEFT JOIN ir_property ir ON "substring"(ir.res_id::text, 18)::integer = product_template.id AND ir.name::text = 'valuation'::text AND ir.company_id = stock_move.company_id
                     LEFT JOIN ir_property ir_product ON "substring"(ir_product.res_id::text, 18)::integer = product_template.id AND ir_product.name::text = 'property_stock_valuation_account_id'::text AND ir_product.company_id = stock_move.company_id
                     LEFT JOIN ir_property ir_category ON "substring"(ir_category.res_id::text, 18)::integer = product_template.categ_id AND ir_category.name::text = 'property_stock_valuation_account_id'::text AND ir_category.company_id = stock_move.company_id
                    WHERE stock_move.state::text = 'done'::text AND source_location.usage::text = 'internal'::text AND product_template.type::text = 'product'::text AND (dest_location.usage::text <> 'internal'::text OR dest_location.usage::text = 'internal'::text AND (replace("substring"(dest_location.complete_name::text, '/(( )*\w*( )*)'::text), ' '::text, ''::text) <> replace("substring"(source_location.complete_name::text, '/(( )*\w*( )*)'::text), ' '::text, ''::text)))
            """)

    @api.model
    def _getdate(self):
        return datetime.date(datetime.date.today().year, 1, 1)

    @api.model
    def _gettoday(self):
        return datetime.date.today()

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    start_date = fields.Date(default=_getdate)
    end_date = fields.Date(default=_gettoday)
    res_company_id = fields.Many2one('res.company', required=True, default=_get_company)
    account_account_id = fields.Many2one('account.account', required=True)

    filter = fields.Selection([('filter_no', 'No Filters'), ('filter_date', 'Date'), ('filter_period', 'Periods')],
                              "Filter by", default='filter_no', required=True)

    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')
    location_id = fields.Many2one('stock.location', 'Locations')

    @api.onchange('warehouse_id')
    def onchange_wh(self):
        if self.warehouse_id.lot_stock_id:
            self.location_id = self.warehouse_id.lot_stock_id

    @api.multi
    def action_print(self):
        if self.start_date > self.end_date:
            raise UserError(_('You can not choose start date greater than to date.'))
        date_now = datetime.date.today().strftime('%Y-%m-%d')
        if self.start_date > date_now:
            raise UserError(_('You can not choose a date in the future .'))
        return self.env['report'].get_action(self, 'btek_report_stock.stock_inventory_nxt')


from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx


class StockInventoryNxt(ReportXlsx):
    _name = 'report.btek_report_stock.stock_inventory_nxt'

    def write_data_nxt(self, ws, data, form):
        ws.set_column(1, 1, 10)
        ws.set_column(2, 2, 15)
        ws.set_column(3, 3, 13)
        ws.set_column(4, 4, 25)
        ws.set_column(5, 5, 7)
        ws.set_column(6, 6, 10)
        ws.set_column(7, 7, 10)
        ws.set_column(8, 8, 15)
        ws.set_column(9, 9, 10)
        ws.set_column(10, 10, 10)
        ws.set_column(11, 11, 15)
        ws.set_column(12, 12, 15)

        # Header
        address = u''
        if self.env.user.company_id.street: address = self.env.user.company_id.street
        if self.env.user.company_id.street2: address = address + ', ' + unicode(self.env.user.company_id.street2)
        if self.env.user.company_id.city: address = address + ', ' + unicode(self.env.user.company_id.city)
        ws.write('A%s' % 1, u'Công ty:', )
        ws.merge_range('B1:E1', self.env.user.company_id.name, self.xxxxx)
        ws.write('A%s' % 2, u'Địa chỉ:', )
        ws.merge_range('B2:E2', address, self.xxxxx)

        ws.merge_range('A4:M4', u'BẢNG TỔNG HỢP CHI TIẾT HÀNG HÓA', self.title)

        ws.merge_range('A5:M5', u'Từ ngày: ' + unicode(
            datetime.datetime.strptime(form.start_date, '%Y-%m-%d').strftime('%d/%m/%Y'))
                       + u' Đến ngày: ' + unicode(
            datetime.datetime.strptime(form.end_date, '%Y-%m-%d').strftime('%d/%m/%Y')), self.header)

        # ws.merge_range('L8:M8', unicode(form.warehouse.name or ' ') or '', self.xxxxx)
        ws.write('K9', u'Tài khoản:', )
        ws.merge_range('L9:M9', unicode(form.account_account_id.code or ' ') or '', self.xxxxx)
        ws.write('K10', u'Tiền tệ:', )
        ws.merge_range('L10:M10', u'VNĐ', self.xxxxx)
        # ws.merge_range('C8:D8', unicode(form.product.name or ' '), self.xxxxx)

        ws.write("A11", u'STT', self.table_header)
        ws.write("B11", u'Mã vật tư', self.table_header)
        ws.merge_range("C11:D11", u'Tên vật tư/ Tên hàng hóa', self.table_header)
        ws.write("E11", u'Tồn đầu', self.table_header)
        ws.write("F11", u'Dư đầu', self.table_header)
        ws.write("G11", u'SL nhập', self.table_header)

        ws.write("H11", u'Tiền nhập', self.table_header)
        ws.write("I11", u'SL xuất', self.table_header)
        ws.write("J11", u'Tiền xuất', self.table_header)
        ws.write("K11", u'Tồn cuối', self.table_header)

        ws.write("L11", u'Dư cuối', self.table_header)
        ws.write("M11", u'Tài khoản kho', self.table_header)

        row = 12
        i = 1
        j = 0
        first_row = row
        sum_dudau = 0.0
        sum_tiennhap = 0.0
        sum_tienxuat = 0.0
        sum_ducuoi = 0.0
        for r in data:
            ws.write("A{row}".format(row=row), i, self.table_row_center)  # stt
            ws.write("B{row}".format(row=row), r['product_code'] or '', self.table_row_left)  # ngay ct
            ws.merge_range("C{row}:D{row}".format(row=row), r['product_name'] or '', self.table_row_left)  # so ct
            ws.write("E{row}".format(row=row), r['soluongdauky'] or 0.0, self.table_row_right)  # dien giai
            ws.write("F{row}".format(row=row), r['giatridau'] or 0.0, self.table_row_right)  # dvt
            ws.write("G{row}".format(row=row), r['soluongnhap'] or 0.0, self.table_row_right)  # slnhap
            ws.write("H{row}".format(row=row), r['giatrinhap'] or 0.0, self.table_row_right)  # sl xuat
            ws.write("I{row}".format(row=row), r['soluongxuat'] or 0.0, self.table_row_right)  # slnhap price
            ws.write("J{row}".format(row=row), r['giatrixuat'] or 0.0, self.table_row_right)  # slnhap price
            ws.write("K{row}".format(row=row), r['soluongtoncuoi'] or 0.0, self.table_row_right)  # ton
            ws.write("L{row}".format(row=row), r['giatritoncuoi'] or 0.0, self.table_row_right)  # ton price
            ws.write("M{row}".format(row=row), r['account_code'], self.table_row_center)  # sl xuat price
            sum_dudau += float(r['giatridau'] or 0.0)
            sum_tiennhap += float(r['giatrinhap'] or 0.0)
            sum_tienxuat += float(r['giatrixuat'] or 0.0)
            sum_ducuoi += float(r['giatritoncuoi'] or 0.0)
            i += 1
            row += 1
            j += 1

        ws.write("E{row}".format(row=row), u'TỔNG', self.bold_title)  # TONG
        ws.write("F{row}".format(row=row), sum_dudau, self.bold_sum)  # du dau
        ws.write("H{row}".format(row=row), sum_tiennhap, self.bold_sum)  # sl nhap
        ws.write("J{row}".format(row=row), sum_tienxuat, self.bold_sum)  # xuat_price
        ws.write("L{row}".format(row=row), sum_ducuoi, self.bold_sum)  # du cuoi price

        row += 2
        ws.merge_range("B{row}:D{row}".format(row=row), u'Ngày mở sổ :.......................', self.left)
        row = row + 1
        ws.merge_range("B{row}:D{row}".format(row=row), u'Ngày.......tháng.......năm.......', self.left)

        row += 2
        ws.merge_range("A{row}:D{row}".format(row=row), u'Người ghi sổ', self.bold_title)
        ws.merge_range("E{row}:I{row}".format(row=row), u'Kế toán trưởng', self.bold_title)
        ws.merge_range("J{row}:M{row}".format(row=row), u'Giám đốc', self.bold_title)

        row = row + 1
        ws.merge_range("A{row}:D{row}".format(row=row), u'(ký, họ tên)', self.center)
        ws.merge_range("E{row}:I{row}".format(row=row), u'(ký, họ tên)', self.center)
        ws.merge_range("J{row}:M{row}".format(row=row), u'(ký, họ tên)', self.center)

    def generate_xlsx_report(self, wb, data, form):
        reports = {
            'report': self.write_data_nxt,
        }
        ws = wb.add_worksheet('Bangtonghop')
        wb.formats[0].font_name = 'Times New Roman'
        wb.formats[0].font_size = 11
        ws.set_paper(9)
        ws.center_horizontally()
        ws.set_margins(left=0.28, right=0.28, top=0.5, bottom=0.5)
        ws.fit_to_pages(1, 0)
        ws.set_landscape()
        ws.fit_to_pages(1, 1)

        # DEFINE FORMATS
        self.bold_title = wb.add_format({
            'bold': 1, 'text_wrap': 1, 'valign': 'vcenter', 'align': 'center', 'font_name': 'Times New Roman',
        })
        self.bold_sum = wb.add_format({
            'bold': 1, 'text_wrap': 1, 'valign': 'vcenter', 'align': 'right', 'font_name': 'Times New Roman',
            'num_format': '#,##0.00'
        })

        self.right = wb.add_format({
            'text_wrap': 1, 'align': 'right', 'text_wrap': 1, 'valign': 'vcenter', 'num_format': '#,##0.00',
            'font_name': 'Times New Roman',
        })
        self.left = wb.add_format({
            'text_wrap': 1, 'align': 'left', 'text_wrap': 1, 'valign': 'vcenter', 'num_format': '#,##0.00',
            'font_name': 'Times New Roman',
        })

        self.center = wb.add_format({
            'text_wrap': 1, 'align': 'center', 'text_wrap': 1, 'valign': 'vcenter', 'font_name': 'Times New Roman',
        })
        self.title = wb.add_format({
            'bold': 1, 'text_wrap': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 18,
            'font_name': 'Times New Roman',
        })
        self.left = wb.add_format({
            'text_wrap': 1, 'align': 'left', 'text_wrap': 1, 'valign': 'vcenter', 'font_name': 'Times New Roman',
        })

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
            'font_size': 18,
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

        self.table_row_center = wb.add_format({
            'text_wrap': 1,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'font_name': 'Times New Roman',
        })
        self.table_row_center_bold = wb.add_format({
            'text_wrap': 1,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'bold': 1,
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

        self.row_date_default = wb.add_format({
            'text_wrap': 1,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'font_name': 'Times New Roman',
            # 'font_size': 11,
            'num_format': 'dd/mm/yyyy'
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

        account_ids = form.account_account_id.ids + form.account_account_id.child_ids.ids
        self.env['stock.inventory.nxt'].init()
        args = {
            'company_name': form.res_company_id.name or '',
            'company_id': form.res_company_id.id or None,
            'start': form.start_date,
            'end': form.end_date,
            'account': form.account_account_id.code or '',
            'account_ids': ','.join(str(x) for x in account_ids),
            'tz': self.get_timezone_offset()
        }
        report_data = self.get_data_query(args)
        reports['report'](ws, report_data, form)

    def get_data_query(self, kwargs):
        data = self.get_query(kwargs)
        return data

    def get_query(self, kwargs):
        parameters = kwargs.copy()
        sql = self.build_sql(parameters)
        return sql

    def build_sql(self, parameters):
        query_str = """
                    WITH tb AS (
                        --Dau ky
                        SELECT sv.code, sv.name, aa.code AS account_code, quantity AS tondau, total_amount AS dudau,
                        NULL::numeric slnhap, NULL::numeric tiennhap, 
                        NULL::numeric slxuat, NULL::numeric tienxuat
                        FROM s11_view sv
                        LEFT JOIN account_account aa ON aa.id=sv.account_id
                        WHERE kieu=FALSE AND sv.company_id = {company_id} 
                        AND (sv.date+ interval '{tz} hour')::date < '{date_from}'
                        AND sv.account_id IN ({account_ids}) 	
                        UNION ALL
                        --Giua ky
                        SELECT sv.code, sv.name, aa.code AS account_code, NULL::numeric tondau, NULL::numeric dudau,
                        CASE WHEN quantity >= 0 THEN quantity ELSE 0 END AS slnhap, CASE WHEN total_amount >= 0 THEN total_amount ELSE 0 END AS tiennhap,
                        CASE WHEN quantity < 0 THEN -quantity ELSE 0 END AS slxuat, CASE WHEN total_amount < 0 THEN -total_amount ELSE 0 END AS tienxuat
                        FROM s11_view sv
                        LEFT JOIN account_account aa ON aa.id=sv.account_id
                        WHERE kieu=FALSE AND sv.company_id = {company_id} 
                        AND (sv.date + interval '{tz} hour')::date  >= '{date_from}' and (sv.date+ interval '{tz} hour')::date <= '{date_to}'
                        AND sv.account_id IN ({account_ids})  
                    )
                    SELECT code product_code, name product_name, account_code, 
                    SUM(tondau) AS soluongdauky, SUM(dudau) AS giatridau, 
                    SUM(slnhap) AS soluongnhap, SUM(tiennhap) AS giatrinhap, 
                    SUM(slxuat) AS soluongxuat, SUM(tienxuat) AS giatrixuat,
                    CASE WHEN SUM(tondau) IS NULL THEN 0 ELSE SUM(tondau) END + 
                    CASE WHEN SUM(slnhap) IS NULL THEN 0 ELSE SUM(slnhap) END -
                    CASE WHEN SUM(slxuat) IS NULL THEN 0 ELSE SUM(slxuat) END                
                    AS soluongtoncuoi, 
                    CASE WHEN SUM(dudau) IS NULL THEN 0 ELSE SUM(dudau) END + 
                    CASE WHEN SUM(tiennhap) IS NULL THEN 0 ELSE SUM(tiennhap) END -
                    CASE WHEN SUM(tienxuat) IS NULL THEN 0 ELSE SUM(tienxuat) END                
                    AS giatritoncuoi
                    FROM tb
                    GROUP BY code, name, account_code
                    ORDER BY code, name, account_code
                """
        query_str = query_str.format(date_from=parameters['start'], date_to=parameters['end'],
                                     company_id=parameters['company_id'],
                                     account_ids=parameters['account_ids'], tz=parameters['tz'])
        self.env.cr.execute(query_str)
        return self.env.cr.dictfetchall()

    def _get_children_and_consol_anhtt(self, ids):
        ids2 = self.env['account.account'].search([('parent_id', 'child_of', ids)])
        ids3 = []
        for rec in self.env['account.account'].browse(ids2):
            for child in rec.child_consol_ids:
                ids3.append(child.id)
        if ids3:
            ids3 = self._get_children_and_consol(ids3)
        return ids2 + ids3

    @api.multi
    def get_timezone_offset(self):
        import pytz
        tz = pytz.timezone(self.env.user.tz or u'Asia/Ho_Chi_Minh').localize(datetime.datetime.now()).strftime('%z')
        # Timezone offset's format is for example: +0700, -1000,...
        return tz[:-2]


StockInventoryNxt('report.btek_report_stock.stock_inventory_nxt', 'stock.inventory.nxt')
