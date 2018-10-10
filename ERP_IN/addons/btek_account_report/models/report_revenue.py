# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
from odoo import tools
from datetime import datetime, timedelta


class ReportReportRevenueXlsx(ReportXlsx):
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
                # .replace(
                # '.', '/').replace(',', '.').replace('/', ',')
            return num_text

        sheet = workbook.add_worksheet(_('Report revenue'))

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

        border_bold = workbook.add_format({'bold': True, 'valign': 'vcenter'})
        border_bold.set_text_wrap()
        border_bold.set_align('center')
        border_bold.set_font_name('Times New Roman')
        border_bold.set_bottom()
        border_bold.set_top()
        border_bold.set_left()
        border_bold.set_right()
        border_bold.set_fg_color('#bcdb0f')
        border_bold.set_font_color('blue')

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

        normal_normal = workbook.add_format({'valign': 'vcenter'})
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

        right_normal_border = workbook.add_format({'valign': 'vcenter'})
        right_normal_border.set_font_name('Times New Roman')
        right_normal_border.set_text_wrap()
        right_normal_border.set_top()
        right_normal_border.set_bottom()
        right_normal_border.set_left()
        right_normal_border.set_right()
        right_normal_border.set_align('right')

        sheet.set_default_row(20)
        sheet.set_column('A:A', 25)
        sheet.set_column('B:B', 12)
        sheet.set_column('C:C', 12)

        product_dict, month_list, total_dict, total, from_date, to_date = wizard.get_data()

        row_pos = 1

        sheet.merge_range(
            'A{row_pos}:I{row_pos}'.format(
                row_pos=row_pos),
            u'BÁO CÁO DOANH THU THEO TỪNG HÀNG MỤC SẢN PHẨM',
            header_bold)

        row_pos += 1

        sheet.merge_range(
            'A{row_pos}:I{row_pos}'.format(
                row_pos=row_pos),
            u'Ngày xuất báo cáo: {}'.format(
                datetime.now().strftime('%d-%m-%Y')),
            bold)

        row_pos += 1

        from_date = datetime.strptime(
            from_date, '%Y-%m-%d').strftime('%d-%m-%Y')
        to_date = datetime.strptime(
            to_date, '%Y-%m-%d').strftime('%d-%m-%Y')

        sheet.merge_range(
            'A{row_pos}:I{row_pos}'.format(
                row_pos=row_pos),
            u'Doanh số từ {} đến {}'.format(
                from_date, to_date),
            bold)

        row_pos += 1

        sheet.merge_range(
            'A{row_pos}:A{row_pos_1}'.format(
                row_pos=row_pos,row_pos_1=row_pos+1),
            u'Tên sản phẩm',
            border_bold)
        sheet.merge_range(
            'B{row_pos}:B{row_pos_1}'.format(
                row_pos=row_pos, row_pos_1=row_pos + 1),
            u'Đơn giá',
            border_bold)
        sheet.merge_range(
            'C{row_pos}:C{row_pos_1}'.format(
                row_pos=row_pos, row_pos_1=row_pos + 1),
            u'Lũy tiến',
            border_bold)

        col = 'D'
        col_index = 3
        for month in month_list:
            sheet.set_column('{}:{}'.format(col, col), 10)

            pre_col = col
            col = self.next_char(col)

            sheet.set_column('{}:{}'.format(col, col), 10)

            sheet.merge_range(
                '{pre_col}{row_pos}:{col}{row_pos}'.format(
                    pre_col=pre_col, col=col, row_pos=row_pos),
                u'Tháng {}'.format(month),
                border_bold)

            col = self.next_char(col)

            sheet.write(row_pos, col_index,
                        u'Số lượng',
                        border_bold)
            col_index += 1
            sheet.write(row_pos, col_index,
                        u'Doanh thu',
                        border_bold)
            col_index += 1

        row_pos += 1

        for product_id in product_dict.keys():
            product_name = product_dict[product_id]['name']
            list_price = product_dict[product_id]['list_price']
            progressive = product_dict[product_id].get('progressive', 0)

            list_price = format_number(list_price)
            progressive = format_number(progressive)

            sheet.write(row_pos, 0, product_name, normal_border)
            sheet.write(row_pos, 1, list_price, right_normal_border)
            sheet.write(row_pos, 2, progressive, right_normal_border)

            col_index = 3
            for month in month_list:
                qty = product_dict[product_id]['balance'].get(month, {}).get('qty', '')
                balance = product_dict[product_id]['balance'].get(month, {}).get('balance', '')
                balance = format_number(balance)

                sheet.write(row_pos, col_index,
                            qty,
                            right_normal_border)
                col_index += 1
                sheet.write(row_pos, col_index,
                            balance,
                            right_normal_border)
                col_index += 1

            row_pos += 1

        sheet.write(row_pos, 0, u'Tổng cộng', footer)
        sheet.write(row_pos, 1, u'', footer)

        total = format_number(total)
        sheet.write(row_pos, 2, total, right_footer)

        col_index = 3
        for month in month_list:
            qty = total_dict.get(month, {}).get('qty', '')
            balance = total_dict.get(month, {}).get('balance', '')

            balance = format_number(balance)

            sheet.write(row_pos, col_index,
                        qty,
                        right_footer)
            col_index += 1
            sheet.write(row_pos, col_index,
                        balance,
                        right_footer)
            col_index += 1


ReportReportRevenueXlsx(
    'report.btek_account_report.report.revenue.xlsx',
    'wizard.report.revenue')
