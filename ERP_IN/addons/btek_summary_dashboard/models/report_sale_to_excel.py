# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import datetime
from operator import itemgetter
from odoo import tools
from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
import json

class Report_sale_to_excel(models.TransientModel):
    _name = 'report.sale.to.excel'

    from_date = fields.Date(required=True)
    to_date = fields.Date(
        required=True,
        default=lambda s:datetime.datetime.now().strftime('%Y-%m-%d'))
    group_by = fields.Selection(
        [
         ('order_id', 'Order'),
         ('date_date_order_str', 'Date'),
         ('product_type', 'Product type'),
         ('partner_id', 'Customer'),
         ('user_id', 'Saleman'),
         ('workorder_user_id', 'Workorder user'),
         ('product_categ_id', 'Product category'),
        ],
        'Group by', required=True,
        default='order_id'
    )
    type = fields.Selection(
        [('in', 'In'),
         ('out', 'Out')],
        'Type', required=True,
        default='in'
    )
    name = fields.Char(required=True)

    _sql_constraints = [
        ('check_from_date_to_date',
         'check(from_date <= to_date)',
         'From date must be less than or equal to date!'),
    ]

    @api.model
    def create(self, vals):
        type = vals['type'] == 'in' and _('in') or _('out')
        vals['name'] = _('Synthesis report revenue car {}.xlsx').format(type)
        return super(Report_sale_to_excel, self).create(vals)

    def get_field_type(self, f):
        model_name = 'bave.sale.report'
        model_bject = self.env[model_name].\
            with_context(lang=self.env.user.partner_id.lang)
        field = model_bject._fields[f]
        if field.type in ('int', 'float'):
            return 'number'
        if field.type in ('date', 'datetime'):
            return field.type

        return 'char'

    @api.model
    def get_tr_selection(self, model_name, field_name):
        uid = self.env.uid
        user = self.env['res.users'].browse(uid)
        model_bject = self.env[model_name].\
            with_context(lang=user.partner_id.lang)
        field = model_bject._fields[field_name]
        selection = field.selection

        tr_dict = self.env['bave.sale.report'].tr(model_name, field_name)

        selection_tr_dict = \
            dict((s[0], tr_dict.get(s[1], s[1])) for s in selection)
        return selection_tr_dict

    def get_field_list(self):
        res = [
            'order_id',
            'license_plate',
            'date_date_order',
            'default_code',
            'product_id',
            'product_uom_qty',
            'price_unit',
            'subtotal_with_out_discount',
            'discount_total',
            'price_subtotal',
            'cost_price',
            'cost_total',
            'profit',
        ]
        if self.type == 'in':
            res.append('state')
        if self.type == 'out':
            res.append('invoice_state')
        return res

    def get_sum_field_list(self):
        sum_field_list = [
            'product_uom_qty',
            'subtotal_with_out_discount',
            'discount_total',
            'price_subtotal',
            'cost_price',
            'cost_total',
            'profit',
        ]
        res = {}
        index = 0
        for f in self.get_field_list():
            if f in sum_field_list:
                res[f] = index
            index += 1
        return res

    def get_field_description_dict(self):
        field_list = self.get_field_list()

        field_s = \
            self.env['ir.model.fields'].search_read(
                [('name', 'in', field_list),
                 ('model_id', '=',
                  self.env.ref('btek_summary_dashboard.model_bave_sale_report').id)],
                ['field_description','name']
            )

        field_description_dict = \
            dict((f['name'], f['field_description']) for f in field_s)

        return field_description_dict

    @api.multi
    def get_data(self):
        domain_dict = {'in':
                           [('upsell', '=', False),
                            ('invoice_confirmed','=', False)],
                       'out':
                           [('upsell', '=', False),
                            ('invoice_confirmed','=', True)]
                       }
        type = self[0].type
        domain = domain_dict[type]
        domain.append(
            ('date_date_order', '>=', self[0].from_date)
        )
        domain.append(
            ('date_date_order', '<=', self[0].to_date)
        )

        field_list = self.get_field_list()
        field_list.append('user_id')
        groupby = self[0].group_by
        if groupby not in field_list:
            field_list.append(groupby)

        line_s = self.env['bave.sale.report'].search_read(domain, field_list)

        invoice_state_selection_dict = \
            self.get_tr_selection('bave.sale.report',
                                  'invoice_state')

        line_group_s = {}

        sum_field_list = self.get_sum_field_list().keys()
        sum_dict = dict((f, 0) for f in sum_field_list)

        for line in line_s:
            groupby_value = line[groupby] or _('Undefine')
            if not line_group_s.get(groupby_value, False):
                line_group_s[groupby_value] = {
                    'sum': {},
                    'count': 0,
                    'item': []
                }
                for f in sum_field_list:
                    line_group_s[groupby_value]['sum'][f] = 0

            line_group_s[groupby_value]['count'] += 1

            for f in sum_field_list:
                f_value = line[f] or 0
                line_group_s[groupby_value]['sum'][f] += \
                    f_value
                sum_dict[f] += f_value
            line_group_s[groupby_value]['item'].append(line)

            if line.get('invoice_state', False):
                line['invoice_state'] = invoice_state_selection_dict.get(line['invoice_state'], line['invoice_state'])

        company = self.env.user.company_id

        return line_s,line_group_s,sum_dict,company

    @api.multi
    def export_report(self):
        datas = {'ids': self.ids}
        datas['model'] = 'report.sale.to.excel'

        type = _('in')
        if self.type == 'out':
            type = _('out')

        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'btek_summary_dashboard.report.sale.to.excel.xlsx',
            'datas': datas,
            'name': _('Sale to excel {}').format(type)
        }

    @api.multi
    def preview_report(self):
        datas = {'ids': self.ids}
        datas['model'] = 'report.sale.to.excel'

        report_name = 'btek_summary_dashboard.report.sale.to.excel.xlsx'
        res = self.env['ir.actions.report.xml'
        ].preview_xlsx_report(report_name, self._ids, datas)
        return res

    @api.multi
    def view_report(self):
        action_id_dict = {
            'in': 'btek_summary_dashboard.action_bave_sale_order_in_report',
            'out': 'btek_summary_dashboard.action_bave_sale_order_out_report',
        }
        action_id = action_id_dict.get(self.type, False)
        if not action_id:
            return True
        action_obj = self.env.ref(action_id)
        action = action_obj.read([])[0]
        domain = eval(action['domain'] or '[]')
        domain.append(
            ('date_date_order', '>=', self.from_date)
        )
        domain.append(
            ('date_date_order', '<=', self.to_date)
        )
        action['domain'] = unicode(domain)
        return action


class ReportReportSaleToExcelXlsx(ReportXlsx):
    def next_char(self, current_char):
        if not current_char:
            return ''

        last_char = current_char[-1]
        prefix = current_char[:len(current_char) - 1]

        if last_char.upper() == 'Z':
            current_char = prefix + 'AA'
            return current_char

        return prefix + chr(ord(last_char) + 1)

    def generate_xlsx_report(self, workbook, data, wizard):
        def format_number(num):
            if type(num) not in (int, float):
                return num
            try:
                num = int(num)
            except:
                pass
            num_text = '{:,}'.format(num)
            return num_text

        sheet = workbook.add_worksheet(_('Detail'))

        header_bold = workbook.add_format({'bold': True, 'valign': 'vcenter'})
        header_bold.set_text_wrap()
        header_bold.set_align('center')
        header_bold.set_font_name('Times New Roman')
        header_bold.set_bottom()
        header_bold.set_top()
        header_bold.set_left()
        header_bold.set_right()
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

        border_bold_right = workbook.add_format(
            {'bold': True,
             'valign': 'vcenter',
             'num_format': '#,##0.00'}
        )
        border_bold_right.set_text_wrap()
        border_bold_right.set_align('right')
        border_bold_right.set_font_name('Times New Roman')
        border_bold_right.set_bottom()
        border_bold_right.set_top()
        border_bold_right.set_left()
        border_bold_right.set_right()

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

        footer = workbook.add_format({'bold': True, 'valign': 'vcenter'})
        footer.set_text_wrap()
        footer.set_font_name('Times New Roman')
        footer.set_bottom()
        footer.set_top()
        footer.set_left()
        footer.set_right()

        right_footer = workbook.add_format({'bold': True, 'valign': 'vcenter'})
        right_footer.set_text_wrap()
        right_footer.set_font_name('Times New Roman')
        right_footer.set_bottom()
        right_footer.set_top()
        right_footer.set_left()
        right_footer.set_right()
        right_footer.set_align('right')

        red_bold_left = workbook.add_format(
            {'bold': True, 'valign': 'vcenter'})
        red_bold_left.set_text_wrap()
        red_bold_left.set_align('left')
        red_bold_left.set_font_name('Times New Roman')
        red_bold_left.set_bottom()
        red_bold_left.set_top()
        red_bold_left.set_left()
        red_bold_left.set_right()
        red_bold_left.set_fg_color('pink')

        orange_bold_left = workbook.add_format(
            {'bold': True, 'valign': 'vcenter'})
        orange_bold_left.set_text_wrap()
        orange_bold_left.set_align('left')
        orange_bold_left.set_font_name('Times New Roman')
        orange_bold_left.set_bottom()
        orange_bold_left.set_top()
        orange_bold_left.set_left()
        orange_bold_left.set_right()
        orange_bold_left.set_fg_color('yellow')

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

        number_normal = workbook.add_format(
            {
                'valign': 'vcenter',
                'num_format': '#,##0.00',
            }
        )

        number_normal.set_font_name('Times New Roman')
        number_normal.set_text_wrap()
        number_normal.set_top()
        number_normal.set_bottom()
        number_normal.set_left()
        number_normal.set_right()
        number_normal.set_align('right')

        normal_border = workbook.add_format({'valign': 'vcenter'})
        normal_border.set_font_name('Times New Roman')
        normal_border.set_text_wrap()
        normal_border.set_top()
        normal_border.set_bottom()
        normal_border.set_left()
        normal_border.set_right()

        left_normal = workbook.add_format({'bold': True, 'valign': 'vcenter'})
        left_normal.set_text_wrap()
        left_normal.set_font_name('Times New Roman')
        left_normal.set_bottom()
        left_normal.set_top()
        left_normal.set_left()
        left_normal.set_right()
        left_normal.set_align('left')

        center_normal = workbook.add_format({'bold': True, 'valign': 'vcenter'})
        center_normal.set_text_wrap()
        center_normal.set_font_name('Times New Roman')
        center_normal.set_bottom()
        center_normal.set_top()
        center_normal.set_left()
        center_normal.set_right()
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
        sheet.set_column('A:A', 11)
        sheet.set_column('B:B', 9)
        sheet.set_column('C:C', 10)
        sheet.set_column('D:D', 10)
        sheet.set_column('E:E', 22)
        sheet.set_column('F:F', 8)
        sheet.set_column('G:G', 12)
        sheet.set_column('H:H', 16)
        sheet.set_column('I:I', 16)
        sheet.set_column('J:J', 16)
        sheet.set_column('K:K', 16)
        sheet.set_column('L:L', 15)
        sheet.set_column('M:M', 15)
        # sheet.set_column('N:N', 15)

        line_s,line_group_s,sum_dict,company = wizard.get_data()
        field_description_dict = wizard.get_field_description_dict()
        field_list = wizard.get_field_list()
        sum_field_dict = wizard.get_sum_field_list()
        sum_field_list = sum_field_dict.keys()

        # print line_s
        # print line_group_s
        # print sum_dict
        # print field_list
        # print sum_field_dict
        # print sum_field_list

        state_selection_dict = \
            wizard.get_tr_selection('sale.order',
                                    'state')

        invoice_state_selection_dict = \
            wizard.get_tr_selection('bave.sale.report',
                                    'invoice_state')

        row_pos = 1
        sheet.merge_range(
            'A{row_pos}:D{row_pos}'.format(
                row_pos=row_pos),
            u'Công ty: {}'.format(company.name),
            left_normal)
        row_pos += 1

        sheet.merge_range(
            'A{row_pos}:D{row_pos}'.format(
                row_pos=row_pos),
            u'Địa chỉ: {}'.format(company.street or ''),
            left_normal)

        row_pos += 1

        report_type = {'in': u'Vào', 'out': u'Ra'}[wizard.type]
        sheet.merge_range(
            'A{row_pos}:I{row_pos}'.format(
                row_pos=row_pos),
            u'Báo Cáo Tổng Hợp Doanh Thu Xe {}'.format(report_type),
            header_bold)

        row_pos += 1
        sheet.merge_range(
            'A{row_pos}:I{row_pos}'.format(
                row_pos=row_pos),
            u'Từ ngày {} đến ngày {}'.format(
                datetime.datetime.strptime(wizard.from_date,'%Y-%m-%d').strftime('%d-%m-%Y'),
                datetime.datetime.strptime(wizard.to_date,'%Y-%m-%d').strftime('%d-%m-%Y'),
            ),
            center_normal)

        col = 0
        for f in field_list:
            field_description = field_description_dict.get(f, '')
            sheet.set_row(row_pos, 32)
            sheet.write(row_pos, col,
                        field_description,
                        header_border_bold)
            col += 1
        row_pos += 1

        def write_lines(line_s, sum_dict, row_pos,
                        sheet, label=['','','',''],
                        index='', state_selection_dict={},
                        invoice_state_selection_dict={},
                        type='out'):
            col = 0
            if index:
                sheet.write(row_pos, col,
                            str(index),
                            border_bold)
                col += 1
            sheet.write(row_pos, col,
                        u'{}({})'.format(label[0], len(line_s)),
                        border_bold)
            col += 1
            sheet.write(row_pos, col,
                        label[1],
                        border_bold)
            col += 1
            sheet.write(row_pos, col,
                        label[2],
                        border_bold)
            col += 1
            sheet.write(row_pos, col,
                        label[3],
                        border_bold)
            col += 1
            sheet.write(row_pos, col,
                        '',
                        border_bold)
            col += 1

            for f in sum_field_list:
                sum_col = sum_field_dict.get(f, 0)
                if sum_col > col:
                    sum_value = sum_dict[f]
                    sheet.write(row_pos, sum_col,
                                sum_value,
                                border_bold_right)

            col += 1
            sheet.write(row_pos, col,
                        '',
                        border_bold)
            # row_pos += 1
            for line in line_s:
                row_pos += 1
                value_list = [self.process_line_value(line[f], f, wizard) for f in field_list]
                value_dict = dict((f, self.process_line_value(line[f], f, wizard)) for f in field_list)

                col = 1
                if not index:
                    col = 0
                for f in field_list:
                    value = value_dict.get(f, '')
                    line_style = normal_normal
                    if wizard.get_field_type(f) == 'number':
                        line_style = number_normal

                    sheet.write(row_pos, col, value,
                                line_style)
                    col += 1

            return row_pos

        detail_sum_dict = {}

        for f in sum_field_list:
            detail_sum_dict[f] = sum([line[f] for line in line_s])

        row_pos = \
            write_lines(line_s, detail_sum_dict, row_pos, sheet,
                        state_selection_dict=state_selection_dict,
                        invoice_state_selection_dict=invoice_state_selection_dict,
                        type=wizard.type)

        row_pos += 1

        ########################################################################
        # sheet2: group
        ########################################################################

        sheet2 = workbook.add_worksheet(_('Group'))
        sheet2.set_default_row(20)
        sheet2.set_column('A:A', 6)
        sheet2.set_column('B:B', 11)
        sheet2.set_column('C:C', 10)
        sheet2.set_column('D:D', 9)
        sheet2.set_column('E:E', 10)
        sheet2.set_column('F:F', 21)
        sheet2.set_column('G:G', 8)
        sheet2.set_column('H:H', 12)
        sheet2.set_column('I:I', 16)
        sheet2.set_column('J:J', 16)
        sheet2.set_column('K:K', 16)
        sheet2.set_column('L:L', 16)
        sheet2.set_column('M:M', 15)
        sheet2.set_column('N:N', 15)

        row_pos = 1
        sheet2.merge_range(
            'A{row_pos}:D{row_pos}'.format(
                row_pos=row_pos),
            u'Công ty: {}'.format(company.name),
            left_normal)
        row_pos += 1

        sheet2.merge_range(
            'A{row_pos}:D{row_pos}'.format(
                row_pos=row_pos),
            u'Địa chỉ: {}'.format(company.street or ''),
            left_normal)

        row_pos += 1

        report_type = {'in': u'Vào', 'out': u'Ra'}[wizard.type]
        sheet2.merge_range(
            'A{row_pos}:I{row_pos}'.format(
                row_pos=row_pos),
            u'Báo Cáo Tổng hợp Doanh Thu Xe {}'.format(report_type),
            header_bold)

        row_pos += 1
        sheet2.merge_range(
            'A{row_pos}:I{row_pos}'.format(
                row_pos=row_pos),
            u'Từ ngày {} đến ngày {}'.format(
                datetime.datetime.strptime(wizard.from_date,
                                           '%Y-%m-%d').strftime('%d-%m-%Y'),
                datetime.datetime.strptime(wizard.to_date,
                                           '%Y-%m-%d').strftime('%d-%m-%Y'),
            ),
            center_normal)

        sheet2.write(row_pos, 0,
                    'STT',
                     header_border_bold)

        col = 1
        for f in field_list:
            field_description = field_description_dict.get(f, '')
            sheet2.set_row(row_pos, 32)
            sheet2.write(row_pos, col,
                         field_description,
                         header_border_bold)

            col += 1
        row_pos += 1

        col = 1

        for f in field_list:
            if f not in sum_field_list:
                col += 1
                continue

            sum_value = sum([line_group_s[group_key]['sum'].get(f, 0) for group_key in line_group_s])
            sheet2.write(row_pos, col,
                         sum_value,
                         border_bold_right)
            col += 1

        count_line = sum([line_group_s[group_key]['count'] for group_key in line_group_s])
        sheet2.write(row_pos, 1,
                     '({})'.format(count_line),
                     border_bold)
        row_pos += 1

        index = 0
        for group_key in line_group_s.keys():
            index += 1
            item_s = line_group_s[group_key]['item']
            count = line_group_s[group_key]['count']
            sum_field_dict = line_group_s[group_key]['sum']

            # group_label = group_key
            # if isinstance(group_key, (list, tuple)):
            #     group_label = group_key[1]

            # license_plate = ''
            # date_date_order_str = ''
            # user_id = ''
            # if item_s and wizard.group_by == 'order_id':
            #     license_plate = item_s[0]['license_plate']
            #     date_date_order_str = item_s[0]['date_date_order_str']
            #     user_id = item_s[0]['user_id'] and item_s[0]['user_id'][1] or ''
            #
            # label = [group_label, license_plate, date_date_order_str, user_id]

            row_pos = self.write_group(
                sheet2, border_bold, border_bold_right, normal_normal,
                number_normal, wizard, sum_field_list,
                group_key, line_group_s, field_list,
                row_pos, sum_field_dict, index=index,
                state_selection_dict=state_selection_dict,
                invoice_state_selection_dict=invoice_state_selection_dict,
                type='out')

    def write_group(self, sheet2, border_bold, border_bold_right, normal_normal,
                    number_normal, wizard, sum_field_list,
                    group_key, line_group_s, field_list,
                    row_pos, sum_field_dict, index='',
                    state_selection_dict={},
                    invoice_state_selection_dict={},
                    type='out'):
        group_item_list = line_group_s[group_key]['item']
        group_item_count = line_group_s[group_key]['count']
        group_item_sum = line_group_s[group_key]['sum']

        col = 0
        if index:
            sheet2.write(row_pos, col,
                        str(index),
                        border_bold)
            col += 1

        group_label_col = col
        sheet2.write(row_pos, group_label_col,
                     u'{}({})'.format(self.process_line_value(group_key),
                                     group_item_count),
                     border_bold)
        for f in field_list:
            if col == group_label_col:
                col += 1
                continue

            if f not in sum_field_list:
                sheet2.write(row_pos, col,
                             '', border_bold)
                col += 1
                continue

            sheet2.write(row_pos, col,
                         group_item_sum.get(f, 0),
                         border_bold_right)
            col += 1
        row_pos += 1

        for group_item in group_item_list:
            col = 0
            if index:
                sheet2.write(row_pos, col, '',
                             normal_normal)
                col += 1

            for f in field_list:
                line_style = normal_normal
                if wizard.get_field_type(f) == 'number':
                    line_style = number_normal

                sheet2.write(row_pos, col,
                             self.process_line_value(group_item.get(f, ''), f, wizard),
                             line_style)
                col += 1
            row_pos += 1
        return row_pos

    def process_line_value(self, value, field_name=False, wizard=False):
        if isinstance(value, (list, tuple)):
            if len(value) > 1:
                return value[1]
        if value == False:
            field_obj = wizard.env['bave.sale.report']._fields[field_name]
            if field_obj.type in ('float', 'integer', 'monetary'):
                return 0
            return ''
        if field_name in ('state', 'invoice_state'):
            selection_dict = \
                wizard.get_tr_selection('sale.order',
                                        field_name)
            value = selection_dict.get(value, value)
            return value
        if value and field_name and wizard:
            field_type = wizard.get_field_type(field_name)
            if field_type not in ('date', 'datetime'):
                return value
            date_format = '%Y-%m-%d'
            new_date_format = '%d-%m-%Y'

            if field_type == 'datetime':
                date_format = '%Y-%m-%d %H:%M:%S'
                new_date_format = '%d-%m-%Y %H:%M:%S'

            value = datetime.datetime.strptime(
                value, date_format).strftime(new_date_format)

        return value

ReportReportSaleToExcelXlsx(
    'report.btek_summary_dashboard.report.sale.to.excel.xlsx',
    'report.sale.to.excel')