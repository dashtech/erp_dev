# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo import tools
import datetime, pytz
from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx


class synthesis_import_export(models.Model):
    _name = 'synthesis.import.export'
    _auto = False

    name = fields.Char()
    code = fields.Char()
    product_id = fields.Many2one('product.product',
                                 'Product')
    categ_id = fields.Many2one('product.category',
                               'Category')
    company_id = fields.Many2one('res.company',
                                 'Company')

    beginning_period_inventory = fields.Float(
        compute='_compute_beginning_period')
    beginning_period_value = fields.Float(
        compute='_compute_beginning_period')
    import_qty = fields.Float(compute='_compute_import')
    import_value = fields.Float(compute='_compute_import')
    export_qty = fields.Float(compute='_compute_export')
    export_value = fields.Float(compute='_compute_export')
    ending_period_inventory = fields.Float(
        compute='_compute_ending_period')
    ending_period_value = fields.Float(
        compute='_compute_ending_period')
    uom_id = fields.Many2one('product.uom', 'Uom')

    @api.multi
    def _compute_beginning_period(self):
        from_date = self.env.context.get('from_date', False)
        location_ids = self.env.context.get('location_ids', False)
        categ_ids = self.env.context.get('categ_ids', False)
        product_ids = self.env.context.get('product_ids', False)
        if not from_date:
            return

        inventory_dict = self.calculate_inventory(
            from_date=False, to_date=from_date,
            location_ids=location_ids, categ_ids=categ_ids,
            product_ids=product_ids)

        for product in self:
            product.beginning_period_inventory = \
                inventory_dict.get(product.product_id.id, 0)
            product.beginning_period_value = \
                product.product_id.standard_price * \
                product.beginning_period_inventory

    @api.multi
    def _compute_import(self):
        context = self.env.context
        inventory_dict = self.calculate_inventory(
            from_date=context.get('from_date', False),
            to_date=context.get('to_date', False),
            location_ids=context.get('location_ids', False),
            categ_ids=context.get('categ_ids', False),
            product_ids=context.get('product_ids', False),
            type='in')

        for product in self:
            product.import_qty = \
                inventory_dict.get(product.product_id.id, 0)
            product.import_value = \
                product.import_qty * \
                product.product_id.standard_price

    @api.multi
    def _compute_export(self):
        context = self.env.context
        inventory_dict = self.calculate_inventory(
            from_date=context.get('from_date', False),
            to_date=context.get('to_date', False),
            location_ids=context.get('location_ids', False),
            categ_ids=context.get('categ_ids', False),
            product_ids=context.get('product_ids', False),
            type='out')

        for product in self:
            product.export_qty = \
                -inventory_dict.get(product.product_id.id, 0)
            product.export_value = \
                -product.export_qty * \
                product.product_id.standard_price

    @api.multi
    def _compute_ending_period(self):
        to_date = self.env.context.get('to_date', False)
        location_ids = self.env.context.get('location_ids', False)
        categ_ids = self.env.context.get('categ_ids', False)
        product_ids = self.env.context.get('product_ids', False)
        if not to_date:
            return

        inventory_dict = self.calculate_inventory(
            from_date=False, to_date=to_date,
            location_ids=location_ids, categ_ids=categ_ids,
            product_ids=product_ids)

        for product in self:
            product.ending_period_inventory = \
                inventory_dict.get(product.product_id.id, 0)
            product.ending_period_value = \
                product.product_id.standard_price * \
                product.ending_period_inventory

    def change_local_datetime_to_utc(self, souce_date):
        user_tz = self.env.user.tz or str(pytz.utc)
        tz_now = datetime.datetime.now(pytz.timezone(user_tz))
        difference = tz_now.utcoffset().total_seconds() / 60 / 60
        difference = int(difference)
        souce_date = datetime.datetime.strptime(
            souce_date, '%Y-%m-%d %H:%M:%S')
        local_date = souce_date + datetime.timedelta(hours=-difference)
        return local_date.strftime('%Y-%m-%d %H:%M:%S')

    def calculate_inventory(
            self, from_date=False, to_date=False,
            location_ids=False, categ_ids=False,
            product_ids=False, type=False):

        from_date = from_date and from_date + ' 00:00:00' or False
        to_date = to_date and to_date + ' 23:59:59' or False

        if from_date:
            from_date = self.change_local_datetime_to_utc(from_date)
        if to_date:
            to_date = self.change_local_datetime_to_utc(to_date)

        from_date_clause = \
            from_date and " and sm.date >= '{}'".format(from_date) or ""
        to_date_clause = \
            to_date and " and sm.date <= '{}'".format(to_date) or ""
        location_clause = location_ids and \
                          " and d.location_id in ({})".format(
                              ','.join([str(location_id) for location_id in location_ids])
                          ) \
                          or ""
        categ_clause = categ_ids and \
                       " and pt.categ_id in ({})".format(
                           ','.join([str(categ_id) for categ_id in categ_ids])
                       ) \
                       or ""
        product_clause = product_ids and \
                       " and pp.id in ({})".format(
                           ','.join([str(product_id) for product_id in product_ids])
                       ) \
                       or ""
        type_clause = ""
        if type:
            type_clause = " and d.type = '{}'".format(type)

        querry = """
            with d as
                (
                select sm.product_id, sm.location_id,
                  sum(-sm.product_uom_qty) as qty, 'out' as type
                from stock_move as sm
                where sm.state = 'done'
                  and sm.company_id = {company_id}
                  {from_date_clause}
                  {to_date_clause}
                group by sm.product_id, sm.location_id
                union
                select sm.product_id, sm.location_dest_id as location_id,
                sum(sm.product_uom_qty) as qty, 'in' as type
                from stock_move as sm
                where sm.state = 'done'
                  and sm.company_id = {company_id}
                  {from_date_clause}
                  {to_date_clause}
                group by sm.product_id, sm.location_dest_id
                )
            select d.product_id, sum(qty) as qty
            from d
            left join product_product as pp on pp.id= d.product_id
            left join product_template as pt on pt.id= pp.product_tmpl_id
            left join stock_location as sl on sl.id = d.location_id
            where sl.usage = 'internal'
            {location_clause}
            {categ_clause}
            {product_clause}
            {type_clause}
            group by d.product_id
        """.format(company_id=self.env.user.company_id.id,
                   from_date_clause=from_date_clause,
                   to_date_clause=to_date_clause,
                   location_clause=location_clause,
                   categ_clause=categ_clause,
                   product_clause=product_clause,
                   type_clause=type_clause)

        self.env.cr.execute(querry)
        result = self.env.cr.dictfetchall()
        inventory_dict = {}
        for row in result:
            product_id = row['product_id']
            qty = row['qty'] or 0

            inventory_dict[product_id] = qty
        return inventory_dict

    @api.model_cr
    def init(self):
        tools.sql.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            """
                CREATE or REPLACE VIEW {} as (
                select max(sm.id) as id, pp.id as product_id,
                  pp.default_code as code, pt.name,
                  pt.uom_id, pt.categ_id, sm.company_id
                from
                  stock_move as sm
                  left join product_product as pp on pp.id = sm.product_id
                  left join product_template as pt on pt.id = pp.product_tmpl_id
                where sm.state = 'done'
                  group by pp.id, pt.name, pt.uom_id, pt.categ_id, sm.company_id
                )
            """.format(self._table)
        )


class wizard_synthesis_import_export(models.TransientModel):
    _name = 'wizard.synthesis.import.export'

    from_date = fields.Date(
        required=True)
    to_date = fields.Date(
        required=True,
        default=datetime.datetime.now().strftime('%Y-%m-%d'))
    location_ids = fields.Many2many(
        'stock.location',
        'wizard_synthesis_import_export_location_rel',
        'wizard_id', 'location_id', 'Locations',
        domain=[('usage', '=', 'internal')]
    )
    categ_ids = fields.Many2many(
        'product.category',
        'wizard_synthesis_import_export_categ_rel',
        'wizard_id', 'category_id', 'Product categories'
    )
    product_ids = fields.Many2many(
        'product.product',
        'wizard_synthesis_import_export_product_rel',
        'wizard_id', 'product_id', 'Products'
    )

    @api.multi
    def view_report(self):
        from_date = self.from_date
        to_date = self.to_date
        location_ids = self.location_ids._ids
        categ_ids = self.categ_ids._ids
        product_ids = self.product_ids._ids

        domain = [('company_id', '=', self.env.user.company_id.id)]
        context = {
            'from_date': from_date,
            'to_date': to_date,
        }

        if categ_ids:
            domain.append(
                ('categ_id', 'in', categ_ids)
            )
            context['categ_ids'] = categ_ids
        if product_ids:
            domain.append(
                ('product_id', 'in', product_ids)
            )
            context['product_ids'] = product_ids
        if location_ids:
            context['location_ids'] = location_ids

        action_obj = self.env.ref(
            'btek_stock.action_synthesis_import_export')
        action = action_obj.read([])[0]
        action['context'] = context
        action['domain'] = domain

        return action

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
    def get_data(self):
        action = self.view_report()
        domain = action['domain']
        context = action['context']

        product_s = self.env['synthesis.import.export'].with_context(context).search(domain)

        company = self.env.user.company_id

        return product_s, company

    @api.multi
    def export_report(self):
        datas = {'ids': self.ids}
        datas['model'] = 'wizard.synthesis.import.export'

        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'btek_stock.wizard.synthesis.import.export.xlsx',
            'datas': datas,
            'name': _('Synthesis import export')
        }

class ReportWizardSynthesisImportExportXlsx(ReportXlsx):
    def generate_xlsx_report(self, workbook, data, wizard):
        sheet = workbook.add_worksheet(_('Detail'))

        header_bold = workbook.add_format(
            {'bold': True, 'valign': 'vcenter'})
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
        sheet.set_column('A:A', 5)
        sheet.set_column('B:B', 15)
        sheet.set_column('C:C', 26)
        sheet.set_column('D:D', 10)
        sheet.set_column('E:E', 16)
        sheet.set_column('F:F', 10)
        sheet.set_column('G:G', 10)
        sheet.set_column('H:H', 16)
        sheet.set_column('I:I', 10)
        sheet.set_column('J:J', 16)
        sheet.set_column('K:K', 10)
        sheet.set_column('L:L', 16)

        product_s, company = \
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
            u'BÁO CÁO TỔNG HỢP NHẬP XUẤT TỒN',
            header_bold)
        row_pos += 1
        sheet.merge_range(
            'A{row_pos}:G{row_pos}'.format(
                row_pos=row_pos),
            u'Từ ngày {} đến ngày {}'.format(wizard.from_date,
                                             wizard.to_date),
            center_normal)
        row_pos += 1
        header_list = ['STT', u'Mã vật tư', u'Tên vật tư/hàng hóa',
                       u'Tồn đầu', u'Dư đầu', u'ĐVT', u'SL nhập',
                       u'Tiền nhập', u'SL xuất', u'Tiền xuất',
                       u'Tồn cuối', u'Dư cuối']
        col = 0
        for header in header_list:
            sheet.write(row_pos, col, header, header_border_bold)
            col += 1
        row_pos += 1
        stt = 0
        for product in product_s:
            stt += 1
            line_value = [
                str(stt), product.code, product.name,
                product.beginning_period_inventory,
                product.beginning_period_value,
                product.uom_id.name,
                product.import_qty,
                product.import_value,
                product.export_qty,
                product.export_value,
                product.ending_period_inventory,
                product.ending_period_value,
            ]
            col = 0
            for value in line_value:
                sheet.write(
                    row_pos, col, value,
                    normal_normal)
                col += 1
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

ReportWizardSynthesisImportExportXlsx(
    'report.btek_stock.wizard.synthesis.import.export.xlsx',
    'wizard.synthesis.import.export')
