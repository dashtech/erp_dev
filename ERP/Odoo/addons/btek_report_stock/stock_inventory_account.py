#!/usr/bin/python
# -*- encoding: utf-8 -*-
# ANHTT
from odoo import api, fields, models, _
import datetime
from datetime import timedelta
from odoo import tools
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class StockInventoryAccount(models.TransientModel):
    _name = 'stock.inventory.account'

    @api.model_cr
    def init(self):
        from odoo import tools
        tools.drop_view_if_exists(self.env.cr, 'stock_move_account_move_line_rel_view')
        self.env.cr.execute("""
                        CREATE OR REPLACE VIEW public.stock_move_account_move_line_rel_view AS 
         WITH tb AS (
                 SELECT sm.id AS stock_move_id,
                    aml.account_id,
                    aml.credit,
                    aml.debit,
                    aml.quantity,
                        CASE
                            WHEN aml.credit > 0::numeric THEN sm.location_id
                            WHEN aml.debit > 0::numeric THEN sm.location_dest_id
                            WHEN aml.debit = 0::numeric AND aml.credit = 0::numeric THEN
                            CASE
                                WHEN dest_location.usage::text = 'internal'::text THEN sm.location_dest_id
                                ELSE sm.location_id
                            END
                            ELSE sm.location_dest_id
                        END AS location_id
                   FROM stock_move sm
                     JOIN stock_location source_location ON sm.location_id = source_location.id
                     JOIN stock_location dest_location ON sm.location_dest_id = dest_location.id
                     LEFT JOIN account_move_line aml ON aml.x_stock_move_id = sm.id
                     LEFT JOIN account_move am ON aml.move_id = am.id
                     LEFT JOIN product_product pp ON pp.id = sm.product_id
                     LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
                     LEFT JOIN ir_property ir_category ON "substring"(ir_category.res_id::text, 18)::integer = pt.categ_id AND ir_category.name::text = 'property_stock_account_output_categ'::text AND ir_category.company_id = sm.company_id
                  WHERE am.state::text = 'posted'::text AND aml.company_id = sm.company_id AND (aml.debit > 0::numeric AND source_location.usage::text <> 'internal'::text AND dest_location.usage::text = 'internal'::text OR aml.credit > 0::numeric AND source_location.usage::text = 'internal'::text AND dest_location.usage::text <> 'internal'::text OR source_location.usage::text = 'internal'::text AND dest_location.usage::text = 'internal'::text OR aml.debit = 0::numeric AND aml.credit = 0::numeric AND
                        CASE
                            WHEN ir_category.value_reference IS NOT NULL THEN "substring"(ir_category.value_reference::text, 17)::integer <> aml.account_id
                            ELSE 1 = 1
                        END AND NOT (aml.account_id IN ( SELECT account_account.id
                           FROM account_account
                          WHERE account_account.company_id = sm.company_id AND account_account.name::text ~~* '%TG%'::text)))
                )
         SELECT tb.stock_move_id,
            tb.account_id,
            tb.location_id,
            sum(tb.credit) AS credit,
            sum(tb.debit) AS debit,
            sum(tb.quantity) AS quantity,
            round(COALESCE(
                CASE
                    WHEN sum(tb.credit) > 0::numeric AND sum(tb.quantity) > 0::numeric THEN sum(tb.credit) / sum(tb.quantity)
                    WHEN sum(tb.debit) > 0::numeric AND sum(tb.quantity) > 0::numeric THEN sum(tb.debit) / sum(tb.quantity)
                    ELSE 0::numeric
                END, 0::numeric), 4) AS price_unit
           FROM tb
          GROUP BY tb.stock_move_id, tb.account_id, tb.location_id;
                        """)

        tools.drop_view_if_exists(self.env.cr, 's10_view')
        self.env.cr.execute("""
         CREATE OR REPLACE VIEW public.s10_view AS 
            SELECT stock_move.id,
            stock_move.id AS move_id,
            dest_location.id AS location_id,
            stock_move.company_id,
            stock_move.product_id,
            product_template.categ_id AS product_categ_id,
                CASE
                    WHEN ir.value_text = 'real_time'::text AND source_location.usage::text <> 'internal'::text AND dest_location.usage::text = 'internal'::text THEN false
                    WHEN ir.value_text = 'real_time'::text AND source_location.usage::text = 'internal'::text AND dest_location.usage::text = 'internal'::text THEN false
                    WHEN ir.value_text = 'real_time'::text AND dest_location.usage::text = 'internal'::text AND source_location.usage::text = 'internal'::text AND replace("substring"(dest_location.complete_name::text, '/(( )*\w*( )*)'::text), ' '::text, ''::text) <> replace("substring"(source_location.complete_name::text, '/(( )*\w*( )*)'::text), ' '::text, ''::text) THEN true
                    WHEN ir.value_text = 'real_time'::text THEN NULL::boolean
                    ELSE NULL::boolean
                END AS kieu,
                CASE
                    WHEN ir.value_text = 'real_time'::text AND source_location.usage::text <> 'internal'::text AND dest_location.usage::text = 'internal'::text THEN sm_acc_line.quantity
                    WHEN ir.value_text = 'real_time'::text AND source_location.usage::text = 'internal'::text AND dest_location.usage::text = 'internal'::text   THEN sm_acc_line.quantity
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
                    WHEN source_location.usage::text = 'internal'::text AND dest_location.usage::text = 'internal'::text THEN sm_acc_line.account_id
                    WHEN dest_location.usage::text = 'internal'::text AND source_location.usage::text = 'internal'::text AND replace("substring"(dest_location.complete_name::text, '/(( )*\w*( )*)'::text), ' '::text, ''::text) <> replace("substring"(source_location.complete_name::text, '/(( )*\w*( )*)'::text), ' '::text, ''::text) THEN
                    CASE
                        WHEN ir_category.value_reference IS NOT NULL THEN "substring"(ir_category.value_reference::text, 17)::integer
                        WHEN ir_product.value_reference IS NOT NULL THEN "substring"(ir_product.value_reference::text, 17)::integer
                        ELSE NULL::integer
                    END
                    ELSE NULL::integer
                END AS account_id,
                CASE
                    WHEN stock_move.picking_id IS NOT NULL THEN stock_picking.date_done
                    WHEN stock_move.inventory_id IS NOT NULL THEN stock_inventory.date
                    ELSE stock_move.date
                END AS date,
                CASE
                    WHEN stock_move.picking_id IS NOT NULL THEN stock_picking.name
                    WHEN stock_move.inventory_id IS NOT NULL THEN stock_inventory.name
                    ELSE stock_move.origin
                END AS so_ct,
            stock_move.product_qty AS quantity_stock_move,
            stock_move.price_unit AS price_unit_stock_move,
            sm_acc_line.debit AS total_amount,
                CASE
                    WHEN stock_move.picking_id IS NOT NULL THEN stock_picking.origin
                    ELSE NULL::character varying
                END AS so_so,
            u.name AS uom,
                CASE
                    WHEN stock_picking.partner_id IS NOT NULL THEN rp.name
                    WHEN stock_move.inventory_id IS NOT NULL THEN dest_location.name
                    ELSE NULL::character varying
                END AS dien_giai,
            stock_move.picking_id,
            stock_move.inventory_id
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
             LEFT JOIN product_uom u ON u.id = product_template.uom_id
             LEFT JOIN res_partner rp ON rp.id = stock_picking.partner_id
            WHERE stock_move.state::text = 'done'::text AND dest_location.usage::text = 'internal'::text AND product_template.type::text = 'product'::text AND (source_location.usage::text <> 'internal'::text OR source_location.usage::text = 'internal'::text AND (replace("substring"(dest_location.complete_name::text, '/(( )*\w*( )*)'::text), ' '::text, ''::text) <> replace("substring"(source_location.complete_name::text, '/(( )*\w*( )*)'::text), ' '::text, ''::text)))
            UNION ALL
            SELECT '-1'::integer * stock_move.id AS id,
            stock_move.id AS move_id,
            source_location.id AS location_id,
            stock_move.company_id,
            stock_move.product_id,
            product_template.categ_id AS product_categ_id,
                CASE
                    WHEN ir.value_text = 'real_time'::text AND source_location.usage::text = 'internal'::text AND dest_location.usage::text <> 'internal'::text THEN false
                    WHEN ir.value_text = 'real_time'::text AND source_location.usage::text = 'internal'::text AND dest_location.usage::text = 'internal'::text  THEN false
                    WHEN ir.value_text = 'real_time'::text AND dest_location.usage::text = 'internal'::text AND source_location.usage::text = 'internal'::text AND replace("substring"(dest_location.complete_name::text, '/(( )*\w*( )*)'::text), ' '::text, ''::text) <> replace("substring"(source_location.complete_name::text, '/(( )*\w*( )*)'::text), ' '::text, ''::text) THEN true
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
                    WHEN ir.value_text = 'real_time'::text AND source_location.usage::text = 'internal'::text AND dest_location.usage::text = 'internal'::text  THEN - sm_acc_line.price_unit::double precision
                    WHEN ir.value_text = 'real_time'::text AND dest_location.usage::text = 'internal'::text AND source_location.usage::text = 'internal'::text AND replace("substring"(dest_location.complete_name::text, '/(( )*\w*( )*)'::text), ' '::text, ''::text) <> replace("substring"(source_location.complete_name::text, '/(( )*\w*( )*)'::text), ' '::text, ''::text) THEN - stock_move.price_unit
                    WHEN ir.value_text = 'real_time'::text THEN NULL::double precision
                    ELSE - stock_move.price_unit
                END AS price_unit_on_quant,
                CASE
                    WHEN source_location.usage::text = 'internal'::text AND dest_location.usage::text <> 'internal'::text THEN sm_acc_line.account_id
                    WHEN source_location.usage::text = 'internal'::text AND dest_location.usage::text = 'internal'::text  THEN sm_acc_line.account_id
                    WHEN dest_location.usage::text = 'internal'::text AND source_location.usage::text = 'internal'::text AND replace("substring"(dest_location.complete_name::text, '/(( )*\w*( )*)'::text), ' '::text, ''::text) <> replace("substring"(source_location.complete_name::text, '/(( )*\w*( )*)'::text), ' '::text, ''::text) THEN
                    CASE
                        WHEN ir_category.value_reference IS NOT NULL THEN "substring"(ir_category.value_reference::text, 17)::integer
                        WHEN ir_product.value_reference IS NOT NULL THEN "substring"(ir_product.value_reference::text, 17)::integer
                        ELSE NULL::integer
                    END
                    ELSE NULL::integer
                END AS account_id,
                CASE
                    WHEN stock_move.picking_id IS NOT NULL THEN stock_picking.date_done
                    WHEN stock_move.inventory_id IS NOT NULL THEN stock_inventory.date
                    ELSE stock_move.date
                END AS date,
                CASE
                    WHEN stock_move.picking_id IS NOT NULL THEN stock_picking.name
                    WHEN stock_move.inventory_id IS NOT NULL THEN stock_inventory.name
                    ELSE stock_move.origin
                END AS so_ct,
            - stock_move.product_qty AS quantity_stock_move,
            - stock_move.price_unit AS price_unit_stock_move,
            - sm_acc_line.credit AS total_amount,
                CASE
                    WHEN stock_move.picking_id IS NOT NULL THEN stock_picking.origin
                    ELSE NULL::character varying
                END AS so_so,
            u.name AS uom,
                CASE
                    WHEN stock_picking.partner_id IS NOT NULL THEN rp.name
                    WHEN stock_move.inventory_id IS NOT NULL THEN source_location.name
                    ELSE NULL::character varying
                END AS dien_giai,
            stock_move.picking_id,
            stock_move.inventory_id
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
             LEFT JOIN product_uom u ON u.id = product_template.uom_id
             LEFT JOIN res_partner rp ON rp.id = stock_picking.partner_id
            WHERE stock_move.state::text = 'done'::text AND source_location.usage::text = 'internal'::text AND product_template.type::text = 'product'::text AND (dest_location.usage::text <> 'internal'::text OR dest_location.usage::text = 'internal'::text AND (replace("substring"(dest_location.complete_name::text, '/(( )*\w*( )*)'::text), ' '::text, ''::text) <> replace("substring"(source_location.complete_name::text, '/(( )*\w*( )*)'::text), ' '::text, ''::text)))
            """)

    def _get_default_date(self):
        import datetime
        return datetime.date(datetime.date.today().year, 1, 1)

    from_date = fields.Date(string="Từ ngày", required=True, default=_get_default_date)
    to_date = fields.Date(string="Đến ngày", required=True, default=fields.Date.context_today)
    location = fields.Many2one("stock.location", string="Vị trí")
    warehouse = fields.Many2one("stock.location", string="Kho")
    product = fields.Many2one("product.product", string="Vật tư")
    lot_id = fields.Many2one("stock.production.lot", string="Lô")
    product_category = fields.Many2one("product.category", string="Nhóm sản phẩm")
    account_account_id = fields.Many2one('account.account', string="Tài khoản")

    @api.onchange('product')
    def onchange_product(self):
        if self.product:
            if self.product.categ_id:
                if self.product.categ_id.property_stock_valuation_account_id:
                    self.account_account_id = self.product.categ_id.property_stock_valuation_account_id

    @api.multi
    def action_print(self):
        if self.from_date > self.to_date:
            raise UserError(_('Please select recipients.'))
        return self.env['report'].get_action(self, 'btek_report_stock.stock_inventory_account')


from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx


class StockInventoryAccount(ReportXlsx):
    _name = 'report.btek_report_stock.stock_inventory_account'

    def write_data_inout(self, ws, data, form):
        # ws.set_column(0, 0, 15)
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
        # ws.set_column(13, 13, 15)
        # ws.set_column(14, 14, 15)
        # ws.set_row(7, 40)

        # Header
        address = u''
        if self.env.user.company_id.street: address = self.env.user.company_id.street
        if self.env.user.company_id.street2: address = address + ', ' + unicode(self.env.user.company_id.street2)
        if self.env.user.company_id.city: address = address + ', ' + unicode(self.env.user.company_id.city)
        ws.write('A%s' % 1, u'Công ty:', )
        ws.merge_range('B1:E1', self.env.user.company_id.name, self.xxxxx)
        ws.write('A%s' % 2, u'Địa chỉ:', )
        ws.merge_range('B2:E2', address, self.xxxxx)

        ws.merge_range('A4:M4', u'THẺ KHO KẾ TOÁN', self.title)

        ws.merge_range('A5:M5', u'Từ ngày: ' + unicode(
            datetime.datetime.strptime(form.from_date, '%Y-%m-%d').strftime('%d/%m/%Y'))
                       + u' Đến ngày: ' + unicode(
            datetime.datetime.strptime(form.to_date, '%Y-%m-%d').strftime('%d/%m/%Y')), self.header)

        ws.merge_range('A8:B8', u'Tên vật tư:', )
        ws.merge_range('A9:B9', u'Nhóm vật tư:', )
        ws.write('K8', u'Kho :', )
        ws.merge_range('L8:M8', unicode(form.warehouse.name or ' ') or '', self.xxxxx)
        ws.write('K9', u'Tài khoản:', )
        if form.account_account_id:
            uni = unicode(form.account_account_id.code) + ' ' + unicode(form.account_account_id.name)
            ws.merge_range('L9:M9', unicode(uni or ' ') or '', self.xxxxx)
        else:
            ws.merge_range('L9:M9', '', self.xxxxx)
        ws.write('K10', u'Tiền tệ:', )
        ws.merge_range('L10:M10', u'VNĐ', self.xxxxx)
        ws.merge_range('C8:D8', unicode(form.product.name or ' '), self.xxxxx)
        ws.merge_range('C9:D9', unicode(form.product.categ_id.display_name or ' '), self.xxxxx)

        ws.merge_range("A11:A12", u'STT', self.table_header)
        ws.merge_range("B11:B12", u'Ngày chứng từ', self.table_header)
        ws.merge_range("C11:C12", u'Số chứng từ', self.table_header)
        ws.merge_range("D11:D12", u'Hồ sơ gốc', self.table_header)
        ws.merge_range("E11:E12", u'Đối tượng', self.table_header)
        ws.merge_range("F11:F12", u'Đơn vị tính', self.table_header)

        ws.merge_range("G11:I11", u'Số lượng', self.table_header)
        ws.write("G12", u'Nhập', self.table_header)
        ws.write("H12", u'Xuất', self.table_header)
        ws.write("I12", u'Tồn', self.table_header)

        ws.merge_range("J11:L11", u'Giá trị', self.table_header)
        ws.write("J12", u'Nhập', self.table_header)
        ws.write("K12", u'Xuất', self.table_header)
        ws.write("L12", u'Tồn', self.table_header)
        ws.merge_range("M11:M12", u'Ký xác nhận của kế toán', self.table_header)

        row = 11
        i = 1
        j = 0
        ton_dau = data[0]
        # write ton dau

        row = 13
        if ton_dau:
            ws.write("A{row}".format(row=row), i, self.table_row_center)  # stt
            ws.merge_range("B{row}:H{row}".format(row=row), u'Tồn đầu', self.table_row_center_bold)
            ws.write("I{row}".format(row=row), ton_dau[0]['quantity'] or 0,
                     self.table_row_right_bold)  # ton
            ws.write("J{row}".format(row=row), '', self.table_row_right_bold)  # slnhap price
            ws.write("K{row}".format(row=row), '', self.table_row_right_bold)  # sl xuat price
            ws.write("L{row}".format(row=row), ton_dau[0]['total_amount'] or 0,
                     self.table_row_right_bold)  # ton price
            ws.write("M{row}".format(row=row), '', self.table_row_right_bold)  # ky nhan ke toan
        else:
            ws.write("A{row}".format(row=row), i, self.table_row_center)  # stt
            ws.merge_range("B{row}:H{row}".format(row=row), u'Tồn đầu', self.table_row_center_bold)
            ws.write("I{row}".format(row=row), 0,
                     self.table_row_right_bold)  # ton
            ws.write("J{row}".format(row=row), '', self.table_row_right_bold)  # slnhap price
            ws.write("K{row}".format(row=row), '', self.table_row_right_bold)  # sl xuat price
            ws.write("L{row}".format(row=row), 0,
                     self.table_row_right_bold)  # ton price
            ws.write("M{row}".format(row=row), '', self.table_row_right_bold)  # ky nhan ke toan

        row += 1
        i += 1
        first_row = row
        tz = self.get_timezone_offset()
        stock_packs = data[1]
        for r in stock_packs:
            if r['kieu']:
                continue

            ws.write("A{row}".format(row=row), i, self.table_row_center)
            if r['date']:
                date_done = datetime.datetime.strptime(r['date'], '%Y-%m-%d %H:%M:%S') + relativedelta(
                    hours=tz and int(tz) or 7)
                ws.write("B{row}".format(row=row), date_done, self.row_date_default)  # ngay ct
            ws.write("C{row}".format(row=row), r['so_ct'] or '', self.table_row_left)  # so ct
            ws.write("D{row}".format(row=row), r['so_so'] or '', self.table_row_left)  # so SO
            ws.write("E{row}".format(row=row), r['dien_giai'] or '', self.table_row_left)  # dien giai
            ws.write("F{row}".format(row=row), r['uom'] or '', self.table_row_left)  # dvt
            if r['id'] > 0:
                ws.write("G{row}".format(row=row), r['quantity'] or '', self.table_row_right)  # slnhap
                ws.write("H{row}".format(row=row), '', self.table_row_right)  # sl xuat
                if r['kieu']:  # noi bo
                    ws.write("J{row}".format(row=row),
                             round((r['quantity'] or 0) * (r['price_unit_on_quant'] or 0), 0),
                             self.table_row_right)  # slnhap price
                else:
                    ws.write("J{row}".format(row=row), r['total_amount'], self.table_row_right)  # slnhap price
                ws.write("K{row}".format(row=row), '', self.table_row_right)  # sl xuat price
            else:
                ws.write("G{row}".format(row=row), '', self.table_row_right)  # slnhap
                ws.write("H{row}".format(row=row), r['quantity'] and -r['quantity'] or '',
                         self.table_row_right)  # sl xuat
                ws.write("J{row}".format(row=row), '', self.table_row_right)  # slnhap price
                if r['kieu']:  # noi bo
                    ws.write("K{row}".format(row=row),
                             round((r['quantity'] or 0) * (r['price_unit_on_quant'] or 0), 0),
                             self.table_row_right)  # slnhap price
                else:
                    ws.write("K{row}".format(row=row), r['total_amount'] and -r['total_amount'] or 0,
                             self.table_row_right)  # slnhap price

            ws.write("I{row}".format(row=row), '=I{row_pre}+G{row}-H{row}'.format(row=row, row_pre=row - 1),
                     self.table_row_right)  # ton
            ws.write("L{row}".format(row=row), '=L{row_pre}+J{row}-K{row}'.format(row=row, row_pre=row - 1),
                     self.table_row_right)  # ton price

            if not r['kieu'] and ((r['quantity'] != r['quantity_stock_move']) or (
                        round(r['price_unit_stock_move'] or 0, 0) != round(r['price_unit_on_quant'] or 0, 0))) and r[
                'so_ct'] and 'LC/' not in r['so_ct']:
                if not r['quantity']:
                    ws.write("M{row}".format(row=row), u'Không tìm thấy hạch toán',
                             self.table_row_left)
                elif r['quantity'] != r['quantity_stock_move']:
                    ws.write("M{row}".format(row=row), u'Lệch số lượng, KT lại hạch toán: ' + str(
                        abs((r['quantity'] or 0) - (r['quantity_stock_move'] or 0))), self.table_row_left)
                elif abs(round((r['price_unit_stock_move'] or 0) * r['quantity_stock_move'], 0) - round(
                                r['total_amount'] or 0, 0)) > 1 and not r['inventory_id']:
                    if abs(round((r['price_unit_stock_move'] or 0) * r['quantity_stock_move'], 0)) - abs(
                            round(r['total_amount'] or 0, 0)) > 1:
                        ws.write("M{row}".format(row=row),
                                 u'Lệch giá trị, KT lại hạch toán: ' + str(abs(
                                     round((r['price_unit_stock_move'] or 0) * r['quantity_stock_move'], 0)) - abs(
                                     round(r['total_amount'] or 0, 0))),
                                 self.table_row_left)  # ky nhan ke toan
            else:
                ws.write("M{row}".format(row=row), '', self.table_row_left)  # ky nhan ke toan
            i += 1
            row += 1
            j += 1

        ws.write("E{row}".format(row=row), u'TỔNG', self.bold_title)  # TONG
        ws.write("G{row}".format(row=row),
                 '=SUM(G{first_row}:G{row})'.format(first_row=first_row - 1, row=row - 1), self.bold_sum)  # slnhap
        ws.write("H{row}".format(row=row),
                 '=SUM(H{first_row}:H{row})'.format(first_row=first_row - 1, row=row - 1), self.bold_sum)  # sl xuat
        ws.write("J{row}".format(row=row),
                 '=SUM(J{first_row}:J{row})'.format(first_row=first_row - 1, row=row - 1),
                 self.bold_sum)  # slnhap_price
        ws.write("K{row}".format(row=row),
                 '=SUM(K{first_row}:K{row})'.format(first_row=first_row - 1, row=row - 1),
                 self.bold_sum)  # sl xuat_price

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
            'report': self.write_data_inout,
        }
        ws = wb.add_worksheet('TheKhoKT')
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

        args = {
            'from_date_view': datetime.datetime.strptime(form.from_date, '%Y-%m-%d').strftime('%d/%m/%Y').decode(
                'unicode-escape'),
            'from_date': (datetime.datetime.strptime(form.from_date, '%Y-%m-%d') - timedelta(days=1)).strftime(
                '%d/%m/%Y').decode(
                'unicode-escape'),
            'to_date': datetime.datetime.strptime(form.to_date, '%Y-%m-%d').strftime('%d/%m/%Y').decode(
                'unicode-escape'),
            'warehouse_name': '',
            'product': 'NULL',
            'product_name': 'NULL',
            'product_code': 'NULL',
            'location': 'NULL',
            'location_name': 'NULL',
            'lot': 'NULL',
            'lot_name': 'NULL',
            'location_ids': 'NULL',
            'tz': self.get_timezone_offset(),
            'product_cate_ids': 'NULL',
            'account_ids': 'NULL',
            'company_ids': self.get_company_ids_str(),
            'product_cate_ids': 'NULL',
        }
        self.env['stock.inventory.account'].init()
        if form.warehouse:
            args.update(warehouse_name=form.warehouse.name)
        if form.product:
            args.update(product=form.product.id, product_name=form.product.name,
                        product_code=form.product.default_code)
        if form.lot_id:
            args.update(lot=form.lot_id.id, lot_name=form.lot_id.name)
        if form.warehouse:
            obj_location = self.env['stock.location'].browse(form.warehouse.id)
            x_locations = self.env['stock.location'].search(
                [('id', 'child_of', obj_location.ids), ('usage', '=', 'internal')]).ids
            location_ids = ','.join(str(x) for x in x_locations)
            args.update(location_ids=location_ids)
        if form.location:
            obj_location = self.env['stock.location'].browse(form.location.id)
            x_locations = self.env['stock.location'].search(
                [('id', 'child_of', obj_location.ids), ('usage', '=', 'internal')]).ids
            location_ids = ','.join(str(x) for x in x_locations)
            args.update(location_ids=location_ids,
                        location_name=form.location.complete_name[form.location.complete_name.index("/") + 1:].strip())
        if form.account_account_id:
            account_ids = form.account_account_id.ids + form.account_account_id.child_ids.ids
            account_ids = ','.join(str(x) for x in account_ids)
            args.update(account_ids=account_ids)
        report_data = self.get_data_from_query(args)
        reports['report'](ws, report_data, form)

    def _get_internal_sublocations(self):
        return self.env['stock.location'].search([('id', 'child_of', self.ids), ('usage', '=', 'internal')])

    def get_data_from_query(self, kwargs):
        data = self.get_query(kwargs)

        return data

    def get_query(self, kwargs):
        parameters_tondau = kwargs.copy()
        ngay = datetime.datetime.strptime(parameters_tondau.get('from_date_view'), '%d/%m/%Y') + relativedelta(days=-1)
        parameters_tondau.update(from_date_view=datetime.date(1900, 1, 1).strftime('%d/%m/%Y'),
                                 to_date=ngay.strftime('%d/%m/%Y'))

        ton_dau = self.get_data_s11(parameters_tondau)
        stock_packs = self.get_data_s10(kwargs)
        return [ton_dau, stock_packs]

    @api.multi
    def get_timezone_offset(self):
        import pytz
        tz = pytz.timezone(self.env.user.tz or u'Asia/Ho_Chi_Minh').localize(datetime.datetime.now()).strftime('%z')
        # Timezone offset's format is for example: +0700, -1000,...
        return tz[:-2]

    def get_data_s10(self, data):
        company_ids = data['company_ids']
        product_id = data['product']
        category_ids = data['product_cate_ids']
        location_ids = data['location_ids']
        date_from = datetime.datetime.strptime(data['from_date_view'], '%d/%m/%Y').strftime('%Y-%m-%d') + ' 00:00:00'
        date_to = datetime.datetime.strptime(data['to_date'], '%d/%m/%Y').strftime('%Y-%m-%d') + ' 23:59:59'
        account_ids = data['account_ids']
        tz = data['tz']

        sql = """
            SELECT *
            FROM s10_view
            WHERE 
            CASE WHEN ({company_ids}) IS NOT NULL THEN company_id IN ({company_ids}) ELSE 1=1 END
            AND CASE WHEN {product_id} IS NOT NULL THEN product_id = {product_id} ELSE 1=1 END
            AND CASE WHEN ({category_ids}) IS NOT NULL THEN product_categ_id IN ({category_ids}) ELSE 1=1 END
            AND CASE WHEN ({account_ids}) IS NOT NULL THEN account_id IN ({account_ids}) ELSE 1=1 END
            AND CASE WHEN ({location_ids}) IS NOT NULL THEN location_id IN ({location_ids}) ELSE 1=1 END
            AND (date + interval '{tz} hour')::date BETWEEN '{date_from}' AND '{date_to}'
            ORDER BY product_id, date, id
        """
        sql = sql.format(company_ids=company_ids, product_id=product_id, category_ids=category_ids, date_from=date_from,
                         date_to=date_to, location_ids=location_ids, account_ids=account_ids, tz=tz)
        self.env.cr.execute(sql)
        return self.env.cr.dictfetchall()

    def get_data_s11(self, data):
        a = 1
        company_ids = data['company_ids']
        product_id = data['product']
        category_ids = data['product_cate_ids']
        location_ids = data['location_ids']
        date_from = datetime.datetime.strptime(data['from_date_view'], '%d/%m/%Y').strftime(
            '%Y-%m-%d') + ' 00:00:00'
        date_to = datetime.datetime.strptime(data['to_date'], '%d/%m/%Y').strftime('%Y-%m-%d') + ' 23:59:59'
        account_ids = data['account_ids']
        tz = data['tz']
        sql = """
            SELECT SUM(CASE WHEN kieu = TRUE THEN quantity_stock_move
                  ELSE quantity END) AS quantity, 
            SUM(CASE WHEN kieu = TRUE THEN CASE WHEN quantity_stock_move<0 AND price_unit_stock_move < 0 THEN -quantity_stock_move*price_unit_stock_move
            ELSE quantity_stock_move*price_unit_stock_move
            END
                  ELSE total_amount END            
            ) total_amount, 
            product_id
            FROM s10_view
            WHERE 
            CASE WHEN ({company_ids}) IS NOT NULL THEN company_id IN ({company_ids}) ELSE 1=1 END
            AND CASE WHEN {product_id} IS NOT NULL THEN product_id = {product_id} ELSE 1=1 END
            AND CASE WHEN ({category_ids}) IS NOT NULL THEN product_categ_id IN ({category_ids}) ELSE 1=1 END
            AND CASE WHEN ({account_ids}) IS NOT NULL THEN account_id IN ({account_ids}) ELSE 1=1 END
            AND CASE WHEN ({location_ids}) IS NOT NULL THEN location_id IN ({location_ids}) ELSE 1=1 END
            AND (date + interval '{tz} hour')::date BETWEEN '{date_from}' AND '{date_to}'
            GROUP BY product_id
            ORDER BY product_id
        """
        sql = sql.format(company_ids=company_ids, product_id=product_id, category_ids=category_ids,
                         date_from=date_from,
                         date_to=date_to, location_ids=location_ids, account_ids=account_ids, tz=tz)
        self.env.cr.execute(sql)
        return self.env.cr.dictfetchall()

    def get_company_ids_str(self):
        company_ids = self.get_company_ids()
        return ','.join(str(id) for id in company_ids)

    def get_company_ids(self):
        company = self.env.user.company_id
        res = [company.id]
        query = "SELECT id FROM res_company WHERE parent_id = %s" % company.id
        self.env.cr.execute(query)
        for r in self.env.cr.dictfetchall():
            res.append(r['id'])
        return res


StockInventoryAccount('report.btek_report_stock.stock_inventory_account', 'stock.inventory.account')
