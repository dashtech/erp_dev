# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
import datetime, pytz
from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx


class Detail_import_export_by_product(models.TransientModel):
    _name = 'detail.import.export.by.product'

    from_date = fields.Date(
        required=True)
    to_date = fields.Date(
        required=True)
    location_ids = fields.Many2many(
        'stock.location',
        'detail_import_export_by_product_location_rel',
        'wizard_id', 'location_id', 'Locations',
        domain=[('usage', '=', 'internal')]
    )
    # category_ids = fields.Many2many(
    #     'product.category',
    #     'detail_import_export_by_product_categ_rel',
    #     'wizard_id', 'category_id', 'Product categories'
    # )
    # product_ids = fields.Many2many(
    #     'product.product',
    #     'detail_import_export_by_product_product_rel',
    #     'wizard_id', 'product_id', 'Products'
    # )
    product_id = fields.Many2one('product.product',
                                 'Product', required=True)

    def change_local_datetime_to_utc(self, souce_date):
        user_tz = self.env.user.tz or str(pytz.utc)
        tz_now = datetime.datetime.now(pytz.timezone(user_tz))
        difference = tz_now.utcoffset().total_seconds() / 60 / 60
        difference = int(difference)
        souce_date = datetime.datetime.strptime(
            souce_date, '%Y-%m-%d %H:%M:%S')
        local_date = souce_date + datetime.timedelta(hours=-difference)
        return local_date.strftime('%Y-%m-%d %H:%M:%S')

    def change_utc_datetime_to_local(self, souce_date):
        user_tz = self.env.user.tz or str(pytz.utc)
        tz_now = datetime.datetime.now(pytz.timezone(user_tz))
        difference = tz_now.utcoffset().total_seconds() / 60 / 60
        difference = int(difference)
        souce_date = datetime.datetime.strptime(
            souce_date, '%Y-%m-%d %H:%M:%S')
        local_date = souce_date + datetime.timedelta(hours=difference)
        return local_date.strftime('%Y-%m-%d %H:%M:%S')

    @api.multi
    def get_data(self):
        company = self.env.user.company_id
        from_date = self[0].from_date
        from_datetime = from_date + ' 00:00:00'
        from_datetime = \
            self.change_local_datetime_to_utc(from_datetime)

        to_date = self[0].to_date
        to_datetime = to_date + ' 23:59:59'
        to_datetime = \
            self.change_local_datetime_to_utc(to_datetime)

        location_ids = self[0].location_ids._ids
        # categ_ids = self[0].category_ids._ids
        # product_ids = self[0].product_ids._ids
        product_id = self[0].product_id.id

        location_where_clause = ""
        if location_ids:
            location_ids_text = \
                ','.join([str(location_id) for location_id in location_ids])
            location_where_clause = \
                """ and (sm.location_id in ({location_ids_text})
                or sm.location_dest_id in ({location_ids_text}))
                """.format(location_ids_text=location_ids_text)


        # categ_where_clause = ""
        # if categ_ids:
        #     categ_ids_text = \
        #         ','.join([str(categ_id) for categ_id in categ_ids])
        #     categ_where_clause = " and pt.categ_id in ({})".format(
        #         categ_ids_text)

        product_where_clause = \
            " and sm.product_id in ({})".format(product_id)
        # if product_ids:
        #     product_ids_text = \
        #         ','.join([str(product_id) for product_id in product_ids])
        #     product_where_clause = " and sm.product_id in ({})".format(
        #         product_ids_text)

        querry = """
            select sm.product_id,
                sm.location_id,
                sl.name as location_name,
                sm.location_dest_id,
                sld.name as location_dest_name,
                pt.categ_id,
                sm.product_uom_qty,
                sm.product_uom,
                sm.price_unit,
                sm.company_id,
                sm.date,
                sm.origin,
                sp.name as picking_name,
                pu.name as uom_name,
                sm.product_uom_qty*sm.price_unit as price_total
            from stock_move as sm
            left join product_product as pp on pp.id = sm.product_id
            left join product_template as pt on pt.id = pp.product_tmpl_id
            left join stock_location as sl on sl.id = sm.location_id
            left join stock_location as sld on sld.id = sm.location_dest_id
            left join stock_picking as sp on sp.id = sm.picking_id
            left join product_uom as pu on pu.id = sm.product_uom
            where sm.state = 'done'
            and (sl.usage = 'internal' or sld.usage = 'internal')
            and sm.company_id = {company_id}
            and sm.date <= '{to_datetime}'
            and sm.date >= '{from_datetime}'
            {location_where_clause}
            {product_where_clause}
        """.format(to_datetime=to_datetime,
                   from_datetime=from_datetime,
                   company_id=company.id,
                   location_where_clause=location_where_clause,
                   product_where_clause=product_where_clause
                   )

        self.env.cr.execute(querry)
        sm_list = self.env.cr.dictfetchall()

        location_name_ids = []
        for sm in sm_list:
            sm['date'] = \
                self.change_utc_datetime_to_local(sm['date'])
            if sm['location_dest_id'] not in location_name_ids:
                location_name_ids.append(sm['location_dest_id'])

            if sm['location_id'] not in location_name_ids:
                location_name_ids.append(sm['location_id'])

        location_s = self.env['stock.location'
        ].search([('id','in', location_name_ids)])

        if location_s:
            location_namegets = location_s.name_get()
            location_dict = dict((location[0], location[1]) for location in location_namegets)
        else:
            location_dict = {}

        return sm_list,location_dict,company

    @api.multi
    def export_report(self):
        datas = {'ids': self.ids}
        datas['model'] = 'detail.import.export.by.product'

        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'btek_stock.detail.import.export.by.product.xlsx',
            'datas': datas,
            'name': _('Detail import export by product')
        }

class ReportDetailImportExportByProductXlsx(ReportXlsx):
    def generate_xlsx_report(self, workbook, data, wizard):
        sheet = workbook.add_worksheet(_('Detail'))

        header_bold = workbook.add_format(
            {'bold': True, 'valign': 'vcenter'}
        )
        header_bold.set_text_wrap()
        header_bold.set_align('center')
        header_bold.set_font_name('Times New Roman')
        # header_bold.set_bottom()
        # header_bold.set_top()
        # header_bold.set_left()
        # header_bold.set_right()
        header_bold.set_font_size(17)
        # header_bold.set_fg_color('#bcdb0f')
        # header_bold.set_font_color('blue')

        bold = workbook.add_format({'bold': True, 'valign': 'vcenter'})
        bold.set_text_wrap()
        bold.set_align('center')
        bold.set_font_name('Times New Roman')
        bold.set_font_size(11)

        border_bold = workbook.add_format(
            {'bold': True,
             'valign': 'vcenter',
             'num_format': '#,##0.00'}
        )
        border_bold.set_text_wrap()
        border_bold.set_align('center')
        border_bold.set_font_name('Times New Roman')
        border_bold.set_bottom()
        border_bold.set_top()
        border_bold.set_left()
        border_bold.set_right()

        header_border_bold = workbook.add_format(
            {'bold': True, 'valign': 'vcenter'})
        header_border_bold.set_text_wrap()
        header_border_bold.set_align('center')
        header_border_bold.set_font_name('Times New Roman')
        header_border_bold.set_bottom()
        header_border_bold.set_top()
        header_border_bold.set_left()
        header_border_bold.set_right()

        center_footer = workbook.add_format(
            {'bold': True, 'italic': True, 'valign': 'vcenter'})
        center_footer.set_text_wrap()
        center_footer.set_font_name('Times New Roman')
        # center_footer.set_bottom()
        # center_footer.set_top()
        # center_footer.set_left()
        # center_footer.set_right()
        center_footer.set_align('center')

        normal = workbook.add_format({'valign': 'vcenter'})
        normal.set_text_wrap()
        normal.set_align('center')
        normal.set_font_name('Times New Roman')

        normal_normal = workbook.add_format(
            {
                'valign': 'vcenter',
                'num_format': '#,##0.00',
            }
        )

        normal_normal.set_font_name('Times New Roman')
        normal_normal.set_text_wrap()
        normal_normal.set_top()
        normal_normal.set_bottom()
        normal_normal.set_left()
        normal_normal.set_right()

        normal_border = workbook.add_format({'valign': 'vcenter'})
        normal_border.set_font_name('Times New Roman')
        normal_border.set_text_wrap()
        normal_border.set_top()
        normal_border.set_bottom()
        normal_border.set_left()
        normal_border.set_right()

        left_normal = workbook.add_format(
            {'bold': True, 'valign': 'vcenter',
             'num_format': '#,##0.00',}
        )
        left_normal.set_text_wrap()
        left_normal.set_font_name('Times New Roman')
        # left_normal.set_bottom()
        # left_normal.set_top()
        # left_normal.set_left()
        # left_normal.set_right()
        left_normal.set_align('left')

        center_normal = workbook.add_format(
            {'bold': True, 'valign': 'vcenter'})
        center_normal.set_text_wrap()
        center_normal.set_font_name('Times New Roman')
        # center_normal.set_bottom()
        # center_normal.set_top()
        # center_normal.set_left()
        # center_normal.set_right()
        center_normal.set_align('center')

        right_normal_border = workbook.add_format(
            {'valign': 'vcenter'})
        right_normal_border.set_font_name('Times New Roman')
        right_normal_border.set_text_wrap()
        right_normal_border.set_top()
        right_normal_border.set_bottom()
        right_normal_border.set_left()
        right_normal_border.set_right()
        right_normal_border.set_align('right')

        sheet.set_default_row(20)
        sheet.set_column('A:A', 6)
        sheet.set_column('B:B', 10)
        sheet.set_column('C:C', 14)
        sheet.set_column('D:D', 20)
        sheet.set_column('E:E', 22)
        sheet.set_column('F:F', 22)
        sheet.set_column('G:G', 12)
        sheet.set_column('H:H', 12)
        sheet.set_column('I:I', 14)
        sheet.set_column('J:J', 18)

        sm_list, location_dict, company = \
            wizard.get_data()

        row_pos = 1
        sheet.merge_range(
            'A{row_pos}:D{row_pos}'.format(
                row_pos=row_pos),
            u'Công ty: {}'.format(company.name),
            left_normal)
        row_pos += 1

        sheet.merge_range(
            'A{row_pos}:E{row_pos}'.format(
                row_pos=row_pos),
            u'Địa chỉ: {}'.format(company.street or ''),
            left_normal)

        row_pos += 1

        sheet.merge_range(
            'A{row_pos}:G{row_pos}'.format(
                row_pos=row_pos),
            u'BÁO CÁO CHI TIẾT VẬT TƯ',
            header_bold)

        row_pos += 1
        sheet.merge_range(
            'A{row_pos}:G{row_pos}'.format(
                row_pos=row_pos),
            u'Mã vật tư [{}]{}'.format(
                wizard.product_id.default_code,
                wizard.product_id.name),
            center_normal)

        row_pos += 1
        sheet.merge_range(
            'A{row_pos}:G{row_pos}'.format(
                row_pos=row_pos),
            u'Từ ngày {} Đến ngày {}'.format(
                wizard.from_date, wizard.to_date),
            center_normal)

        row_pos += 1
        header_list = [u'STT', u'Mã chứng từ', u'Ngày tháng',
                       u'Số phiếu nhập/Xuất', u'Kho đến',
                       u'Kho đi', u'ĐVT', u'Số lượng',
                       u'Đơn giá', u'Thành tiền']
        col = 0
        for header in header_list:
            sheet.write(row_pos, col, header, header_border_bold)
            col += 1

        row_pos += 1

        stt = 0
        for sm in sm_list:
            stt += 1

            location_dest_name = \
                location_dict.get(sm['location_dest_id'], 0) \
                or sm['location_dest_name']
            location_name = \
                location_dict.get(sm['location_id'], 0) \
                or sm['location_name']

            value_list = [
                str(stt),
                sm['origin'],
                sm['date'],
                sm['picking_name'],
                location_dest_name,
                location_name,
                sm['uom_name'],
                sm['product_uom_qty'] or 0,
                sm['price_unit'] or 0,
                sm['price_total'] or 0,
            ]
            col = 0
            for value in value_list:
                sheet.write(row_pos, col, value, normal_normal)
                col += 1

            row_pos += 1

        row_pos += 1
        dnow = datetime.datetime.now()
        sheet.merge_range('E{}:G{}'.format(row_pos,row_pos),
                          u'........., Ngày {}  tháng {}  năm {} '.format(
                              dnow.day, dnow.month, dnow.year
                          ), center_footer)
        row_pos += 1
        sheet.merge_range('E{}:G{}'.format(row_pos,row_pos),
                          u'NGƯỜI LẬP BIỂU', center_normal)

ReportDetailImportExportByProductXlsx(
    'report.btek_stock.detail.import.export.by.product.xlsx',
    'detail.import.export.by.product')
