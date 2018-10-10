# -*- coding: utf-8 -*-
from odoo import fields, models, api, _, tools
import datetime, pytz
from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx


class synthesis_stock_inventory(models.Model):
    _name = 'synthesis.stock.inventory'
    _auto = False

    location_id = fields.Many2one('stock.location', 'Location')
    categ_id = fields.Many2one('product.category', 'Category')
    product_id = fields.Many2one('product.product', 'Product')
    company_id = fields.Many2one('res.company', 'Company')
    code = fields.Char()
    name = fields.Char()
    qty = fields.Float(compute='_compute_qty')
    standard_price = fields.Float(related='product_id.standard_price',
                                  string='Price')
    price_total = fields.Float(compute='_compute_qty')

    def change_local_datetime_to_utc(self, souce_date):
        user_tz = self.env.user.tz or str(pytz.utc)
        tz_now = datetime.datetime.now(pytz.timezone(user_tz))
        difference = tz_now.utcoffset().total_seconds() / 60 / 60
        difference = int(difference)
        souce_date = datetime.datetime.strptime(
            souce_date, '%Y-%m-%d %H:%M:%S')
        local_date = souce_date + datetime.timedelta(hours=-difference)
        return local_date.strftime('%Y-%m-%d %H:%M:%S')

    @api.multi
    def _compute_qty(self):
        to_date = self.env.context.get('to_date', False) \
                  or datetime.datetime.now().strftime('%Y-%m-%d')
        to_date = to_date + ' 23:59:59'
        if to_date:
            to_date = self.change_local_datetime_to_utc(to_date)

        location_ids = self.env.context.get('location_ids', False)
        categ_ids = self.env.context.get('categ_ids', False)
        product_ids = self.env.context.get('product_ids', False)

        location_clause = location_ids and \
                          " and sm.location_id in ({})".format(
                              ','.join([str(location_id) for location_id in
                                        location_ids])
                          ) \
                          or ""
        location_dest_clause = \
            location_clause.replace('location_id', 'location_dest_id')

        categ_clause = categ_ids and \
                       " and pt.categ_id in ({})".format(
                           ','.join([str(categ_id) for categ_id in categ_ids])
                       ) \
                       or ""
        product_clause = product_ids and \
                         " and pp.id in ({})".format(
                             ','.join([str(product_id) for product_id in
                                       product_ids])
                         ) \
                         or ""

        querry = """
                  with d as (
                    select sm.product_id,
                      sm.location_id,
                      sum(-sm.product_uom_qty) as qty
                    from stock_move as sm
                      left join product_product as pp on pp.id = sm.product_id
                      left join product_template as pt on pt.id = pp.product_tmpl_id
                      left join stock_location as sl on sl.id = sm.location_id
                    where sm.state = 'done'
                      and sl.usage = 'internal'
                      and sm.date <= '{to_date}'
                      and sm.company_id = {company_id}
                      {location_clause}
                      {categ_clause}
                      {product_clause}
                    group by sm.product_id, pt.categ_id, sm.location_id, sm.company_id
                    union
                    select sm.product_id,
                      sm.location_dest_id as location_id,
                      sum(sm.product_uom_qty) as qty
                    from stock_move as sm
                     left join product_product as pp on pp.id = sm.product_id
                     left join product_template as pt on pt.id = pp.product_tmpl_id
                     left join stock_location as sl on sl.id = sm.location_dest_id
                    where sm.state = 'done'
                      and sl.usage = 'internal'
                      and sm.date <= '{to_date}'
                      and sm.company_id = {company_id}
                      {location_dest_clause}
                      {categ_clause}
                      {product_clause}
                    group by sm.product_id, pt.categ_id, sm.location_dest_id, sm.company_id
                  )
                select product_id, location_id, sum(qty) as qty
                from d
                group by product_id, location_id
                """.format(to_date=to_date,
                           company_id=self.env.user.company_id.id,
                           location_clause=location_clause,
                           location_dest_clause=location_dest_clause,
                           categ_clause=categ_clause,
                           product_clause=product_clause)

        self.env.cr.execute(querry)
        result = self.env.cr.dictfetchall()
        inv_dict = {}
        for r in result:
            location_id = r['location_id']
            product_id = r['product_id']
            qty = r['qty']
            if not inv_dict.get(location_id, False):
                inv_dict[location_id] = {}

            inv_dict[location_id][product_id] = qty

        for line in self:
            line.qty = inv_dict.get(line.location_id.id, {}).get(line.product_id.id, 0)
            line.price_total = line.standard_price*line.qty

    @api.model_cr
    def init(self):
        tools.sql.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            """
                CREATE or REPLACE VIEW {} as (
                with d as (
                select max(sm.id) as id,
                  sm.product_id,
                  pp.default_code as code,
                  pt.name,
                  pt.categ_id,
                  sm.location_id,
                  sm.company_id
                from stock_move as sm
                  left join product_product as pp on pp.id = sm.product_id
                  left join product_template as pt on pt.id = pp.product_tmpl_id
                  left join stock_location as sl on sl.id = sm.location_id
                where sm.state = 'done'
                  and sl.usage = 'internal'
                group by sm.product_id, pp.default_code,
                  pt.name, pt.categ_id, sm.location_id, sm.company_id
                union
                select max(sm.id) as id,
                  sm.product_id,
                  pp.default_code as code,
                  pt.name,
                  pt.categ_id,
                  sm.location_dest_id as location_id,
                  sm.company_id
                from stock_move as sm
                 left join product_product as pp on pp.id = sm.product_id
                 left join product_template as pt on pt.id = pp.product_tmpl_id
                 left join stock_location as sl on sl.id = sm.location_dest_id
                where sm.state = 'done'
                  and sl.usage = 'internal'
                group by sm.product_id, pp.default_code,
                  pt.name,pt.categ_id, sm.location_dest_id, sm.company_id
                  )
                select max(id)as id,
                  product_id,
                  code,
                  name,
                  categ_id,
                  location_id,
                  company_id
                from d
                group by product_id,
                  code,
                  name,
                  categ_id,
                  location_id,
                  company_id
                )
            """.format(self._table))


class wizard_synthesis_stock_inventory(models.TransientModel):
    _name = 'wizard.synthesis.stock.inventory'

    to_date = fields.Date(
        required=True,
        default=datetime.datetime.now().strftime('%Y-%m-%d'))
    location_ids = fields.Many2many(
        'stock.location',
        'wizard_synthesis_stock_inventory_location_rel',
        'wizard_id', 'location_id', 'Locations',
        domain=[('usage', '=', 'internal')]
    )
    category_ids = fields.Many2many(
        'product.category',
        'wizard_synthesis_stock_inventory_categ_rel',
        'wizard_id', 'category_id', 'Product categories'
    )
    product_ids = fields.Many2many(
        'product.product',
        'wizard_synthesis_stock_inventory_product_rel',
        'wizard_id', 'product_id', 'Products'
    )

    def change_local_datetime_to_utc(self, souce_date):
        user_tz = self.env.user.tz or str(pytz.utc)
        tz_now = datetime.datetime.now(pytz.timezone(user_tz))
        difference = tz_now.utcoffset().total_seconds() / 60 / 60
        difference = int(difference)
        souce_date = datetime.datetime.strptime(
            souce_date, '%Y-%m-%d %H:%M:%S')
        local_date = souce_date + datetime.timedelta(hours=-difference)
        return local_date.strftime('%Y-%m-%d %H:%M:%S')

    @api.multi
    def view_report(self):
        action_obj = \
            self.env.ref('btek_stock.action_synthesis_stock_inventory')
        action = action_obj.read([])[0]
        action['domain'] = [('company_id', '=', self.env.user.company_id.id)]
        if self.location_ids:
            action['domain'].append(
                ('location_id', 'in', self.location_ids._ids)
            )
        if self.category_ids:
            action['domain'].append(
                ('categ_id', 'in', self.category_ids._ids)
            )
        if self.product_ids:
            action['domain'].append(
                ('product_id', 'in', self.product_ids._ids)
            )

        action['context'] = {
            'to_date': self.to_date,
            'location_ids': self.location_ids._ids or False,
            'categ_ids': self.category_ids._ids or False,
            'product_ids': self.product_ids._ids or False,
            'search_default_group_location_id': True,
            'search_default_group_categ_id': True,
            'auto_expand': 1,
        }

        return action

    @api.multi
    def get_data(self):
        company = self.env.user.company_id
        to_date = self[0].to_date
        to_datetime = to_date + ' 23:59:59'
        to_datetime = \
            self.change_local_datetime_to_utc(to_datetime)

        location_ids = self[0].location_ids._ids
        categ_ids = self[0].category_ids._ids
        product_ids = self[0].product_ids._ids

        location_where_clause = ""
        location_dest_where_clause = ""
        if location_ids:
            location_ids_text = \
                ','.join([str(location_id) for location_id in location_ids])
            location_where_clause = \
                " and sm.location_id in ({})".format(
                    location_ids_text)
            location_dest_where_clause = \
                " and sm.location_dest_id in ({})".format(
                    location_ids_text)

        categ_where_clause = ""
        if categ_ids:
            categ_ids_text = \
                ','.join([str(categ_id) for categ_id in categ_ids])
            categ_where_clause = " and pt.categ_id in ({})".format(
                categ_ids_text)

        product_where_clause = ""
        if product_ids:
            product_ids_text = \
                ','.join([str(product_id) for product_id in product_ids])
            product_where_clause = " and sm.product_id in ({})".format(
                product_ids_text)

        querry = """
            with d as (
            select sm.product_id, sl.name as location_name, sm.location_dest_id as location_id, pt.categ_id, sm.product_uom_qty, sm.price_unit, sm.company_id, sm.date, sm.product_uom_qty*sm.price_unit as price_total
            from stock_move as sm
            left join product_product as pp on pp.id = sm.product_id
            left join product_template as pt on pt.id = pp.product_tmpl_id
            left join stock_location as sl on sl.id = sm.location_dest_id
            where sm.state = 'done'
            and sl.usage = 'internal'
            and sm.company_id = {company_id}
            and sm.date <= '{to_date}'
            {location_dest_where_clause}
            {categ_where_clause}
            {product_where_clause}
            union all
            select sm.product_id, sl.name as location_name, sm.location_id, pt.categ_id, -sm.product_uom_qty, sm.price_unit, sm.company_id, sm.date, sm.product_uom_qty*sm.price_unit as price_total
            from stock_move as sm
            left join product_product as pp on pp.id = sm.product_id
            left join product_template as pt on pt.id = pp.product_tmpl_id
            left join stock_location as sl on sl.id = sm.location_id
            where sm.state = 'done'
            and sl.usage = 'internal'
            and sm.company_id = {company_id}
            and sm.date <= '{to_date}'
            {location_where_clause}
            {categ_where_clause}
            {product_where_clause}
            )
            select d.product_id,
              d.categ_id,
              d.location_id,
              d.company_id,
              d.location_name,
              sum(d.product_uom_qty) as qty,
              sum(d.price_total) as price_total
            from d
            group by d.product_id, d.location_id, d.company_id, d.location_name, d.categ_id
        """.format(to_date=to_datetime,
                   company_id=company.id,
                   location_dest_where_clause=location_dest_where_clause,
                   location_where_clause=location_where_clause,
                   categ_where_clause=categ_where_clause,
                   product_where_clause=product_where_clause
                   )

        self.env.cr.execute(querry)
        inv_list = self.env.cr.dictfetchall()

        location_name_dict = {}

        categ_ids = []
        product_ids = []
        location_ids = []
        location_dict = {}
        for inv in inv_list:
            product_id= inv['product_id']
            categ_id = inv['categ_id']
            location_id = inv['location_id']
            # company_id = inv['company_id']
            qty = inv['qty']
            # price_total = inv['price_total']

            location_name_dict[location_id] = inv['location_name']

            if location_id not in location_ids:
                location_ids.append(location_id)

            if categ_id not in categ_ids:
                categ_ids.append(categ_id)

            if product_id not in product_ids:
                product_ids.append(product_id)

            if not location_dict.get(location_id, False):
                location_dict[location_id] = {}

            if not location_dict[location_id].get(categ_id, False):
                location_dict[location_id][categ_id] = {}

            if not location_dict[location_id][categ_id].get(product_id, False):
                location_dict[location_id][categ_id][product_id] = {
                    'qty': 0
                }

            location_dict[location_id][categ_id][product_id]['qty'] += qty

        location_s = \
            self.env['stock.location'].search_read([('id', 'in', location_ids)], ['name'])
        for location in location_s:
            location_name_dict[location['id']] = location['name']

        categ_s = self.env['product.category'].browse(categ_ids)
        categ_dict = dict((categ.id, categ.name) for categ in categ_s)

        product_s = self.env['product.product'].browse(product_ids)
        product_dict = \
            dict((product.id, product) for product in product_s)

        sum_dict = {}
        for location_id in location_dict.keys():
            sum_dict[location_id] = {
                'qty': 0,
                'price_total': 0
            }
            for categ_id in location_dict[location_id].keys():
                for product_id in location_dict[location_id][categ_id].keys():
                    qty = location_dict[location_id][categ_id][product_id]['qty']
                    product = product_dict.get(product_id, False)
                    if not product:
                        continue

                    standard_price = product.standard_price
                    price_total = standard_price*qty

                    sum_dict[location_id]['qty'] += qty
                    sum_dict[location_id]['price_total'] += price_total

        return location_dict,location_name_dict,categ_dict,product_dict,sum_dict,company

    @api.multi
    def export_report(self):
        datas = {'ids': self.ids}
        datas['model'] = 'wizard.synthesis.stock.inventory'

        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'btek_stock.wizard.synthesis.stock.inventory.xlsx',
            'datas': datas,
            'name': _('Synthesis stock inventory')
        }

class ReportWizardSynthesisStockInventoryXlsx(ReportXlsx):
    def generate_xlsx_report(self, workbook, data, wizard):
        sheet = workbook.add_worksheet(_('Detail'))

        header_bold = workbook.add_format({'bold': True, 'valign': 'vcenter'})
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
        # border_bold.set_fg_color('#99ccff')
        # border_bold.set_font_color('blue')

        header_border_bold = workbook.add_format({'bold': True, 'valign': 'vcenter'})
        header_border_bold.set_text_wrap()
        header_border_bold.set_align('center')
        header_border_bold.set_font_name('Times New Roman')
        header_border_bold.set_bottom()
        header_border_bold.set_top()
        header_border_bold.set_left()
        header_border_bold.set_right()
        # header_border_bold.set_fg_color('#66ff99')
        # header_border_bold.set_font_color('blue')

        center_footer = workbook.add_format({'bold': True, 'italic': True,
                                            'valign': 'vcenter'})
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

        center_normal = workbook.add_format({'bold': True, 'valign': 'vcenter'})
        center_normal.set_text_wrap()
        center_normal.set_font_name('Times New Roman')
        # center_normal.set_bottom()
        # center_normal.set_top()
        # center_normal.set_left()
        # center_normal.set_right()
        center_normal.set_align('center')

        right_normal_border = workbook.add_format({'valign': 'vcenter'})
        right_normal_border.set_font_name('Times New Roman')
        right_normal_border.set_text_wrap()
        right_normal_border.set_top()
        right_normal_border.set_bottom()
        right_normal_border.set_left()
        right_normal_border.set_right()
        right_normal_border.set_align('right')

        sheet.set_default_row(20)
        sheet.set_column('A:A', 18)
        sheet.set_column('B:B', 18)
        sheet.set_column('C:C', 11)
        sheet.set_column('D:D', 28)
        sheet.set_column('E:E', 7)
        sheet.set_column('F:F', 12)
        sheet.set_column('G:G', 14)

        location_dict, location_name_dict, \
        categ_dict, product_dict, sum_dict, company = \
            wizard.get_data()

        row_pos = 1
        sheet.merge_range(
            'A{row_pos}:C{row_pos}'.format(
                row_pos=row_pos),
            u'Công ty: {}'.format(company.name),
            left_normal)
        row_pos += 1

        sheet.merge_range(
            'A{row_pos}:C{row_pos}'.format(
                row_pos=row_pos),
            u'Địa chỉ: {}'.format(company.street or ''),
            left_normal)

        row_pos += 1

        sheet.merge_range(
            'A{row_pos}:G{row_pos}'.format(
                row_pos=row_pos),
            u'BẢNG TỒN KHO CHI TIẾT VẬT TƯ HÀNG HÓA THEO KHO',
            header_bold)

        row_pos += 1
        sheet.merge_range(
            'A{row_pos}:G{row_pos}'.format(
                row_pos=row_pos),
            u'Đến ngày {}'.format(wizard.to_date),
            center_normal)

        row_pos += 1
        header_list = [u'Kho vật tư', u'Nhóm vật tư',
                       u'Mã vật tư', u'Tên vật tư',
                       u'Số lượng', u'Đơn giá', u'Thành tiền']
        col = 0
        for header in header_list:
            sheet.write(row_pos, col, header, header_border_bold)
            col += 1

        row_pos += 1

        for location_id in location_dict.keys():
            location_name = location_name_dict.get(location_id, '')
            location_qty = sum_dict.get(location_id, {}).get('qty')
            location_price_total = sum_dict.get(location_id, {}).get('price_total')

            sheet.write(row_pos, 0, location_name, left_normal)
            sheet.write(row_pos, 4, location_qty, left_normal)
            sheet.write(row_pos, 6, location_price_total, left_normal)
            sheet.merge_range('B{row_pos}:D{row_pos}'.format(row_pos=row_pos+1),
                              '', left_normal)

            row_pos += 1

            for categ_id in location_dict[location_id].keys():
                categ_name = categ_dict.get(categ_id, '')
                sheet.write(row_pos, 0, '', left_normal)
                sheet.write(row_pos, 1, categ_name, left_normal)
                sheet.merge_range(
                    'C{row_pos}:G{row_pos}'.format(row_pos=row_pos + 1),
                    '', left_normal)

                row_pos += 1

                for product_id in location_dict[location_id][categ_id].keys():
                    qty = location_dict[location_id][categ_id][product_id]['qty']
                    product = product_dict.get(product_id, False)
                    if not product:
                        continue

                    sheet.merge_range(
                        'A{row_pos}:B{row_pos}'.format(row_pos=row_pos + 1),
                        '', normal_normal)

                    sheet.write(row_pos, 2, product.default_code, normal_normal)
                    sheet.write(row_pos, 3, product.name, normal_normal)
                    sheet.write(row_pos, 4, qty, normal_normal)

                    standard_price = product.standard_price
                    price_total = qty * standard_price

                    sheet.write(row_pos, 5, standard_price, normal_normal)
                    sheet.write(row_pos, 6, price_total, normal_normal)

                    row_pos += 1

        row_pos += 2
        dnow = datetime.datetime.now()
        sheet.merge_range('E{}:G{}'.format(row_pos,row_pos),
                          u'........., Ngày {}  tháng {}  năm {} '.format(
                              dnow.day, dnow.month, dnow.year
                          ), center_footer)
        row_pos += 1
        sheet.merge_range('E{}:G{}'.format(row_pos,row_pos),
                          u'NGƯỜI LẬP BIỂU', center_normal)

ReportWizardSynthesisStockInventoryXlsx(
    'report.btek_stock.wizard.synthesis.stock.inventory.xlsx',
    'wizard.synthesis.stock.inventory')
