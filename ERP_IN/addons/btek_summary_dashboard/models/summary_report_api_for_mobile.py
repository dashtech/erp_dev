# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import datetime
from operator import itemgetter


class Summary_report_api_for_mobile(models.Model):
    _name = "summary.report.api"
    _auto = False

    def get_main_report_datas(self, type='revenue', **kw):
        local_years_now = self.env[
            'change.datetime'].change_utc_to_local_datetime(
            datetime.datetime.strftime(datetime.datetime.now(),
                                       '%Y-%m-%d %H:%M:%S'), '%Y')
        start_time_of_years = local_years_now + '-01-01 00:00:00'
        start_time_of_years_utc = self.env[
            'change.datetime'].change_local_datetime_to_utc(
            start_time_of_years, '%Y-%m-%d %H:%M:%S')
        local_month_now = self.env['change.datetime'].change_utc_to_local_datetime(datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S'), '%Y-%m')
        start_time_of_month = local_month_now + '-01 00:00:00'
        start_time_of_month_utc = self.env['change.datetime'].change_local_datetime_to_utc(start_time_of_month, '%Y-%m-%d %H:%M:%S')
        local_date_now = self.env['change.datetime'].change_utc_to_local_datetime(datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S'), '%Y-%m-%d')
        start_time_today = local_date_now + ' 00:00:00'
        start_time_today_utc = self.env['change.datetime'].change_local_datetime_to_utc(start_time_today, '%Y-%m-%d %H:%M:%S')
        start_time_last_day_utc = datetime.datetime.strptime(start_time_today_utc, '%Y-%m-%d %H:%M:%S') - datetime.timedelta(days=1)
        start_time_last_day_utc_strf = datetime.datetime.strftime(start_time_last_day_utc, '%Y-%m-%d %H:%M:%S')

        current_day_temp_revenue = self.get_temporary_revenue(start_time_today_utc, to_time=None)
        last_day_temp_revenue = self.get_temporary_revenue(start_time_last_day_utc_strf, start_time_today_utc)
        current_month_temp_revenue = self.get_temporary_revenue(start_time_of_month_utc, to_time=None)
        current_years_temp_revenue = self.get_temporary_revenue(start_time_of_years_utc, to_time=None)

        if current_day_temp_revenue > last_day_temp_revenue:
            compare_revenue = 'greater'
        elif current_day_temp_revenue == last_day_temp_revenue:
            compare_revenue = 'equal'
        else:
            compare_revenue = 'less'
        compare_revenue_today_lastday = ''
        if last_day_temp_revenue == 0:
            if current_day_temp_revenue == 0:
                compare_revenue_today_lastday = '(↗ 0%)'
            else:
                compare_revenue_today_lastday = '(↗)'
        else:
            compare_revenue_today_lastday_num = ((current_day_temp_revenue - last_day_temp_revenue) / last_day_temp_revenue) * 100
            compare_revenue_today_lastday_num = float("{0:.1f}".format(compare_revenue_today_lastday_num))
            compare_revenue_today_lastday_num_format = '{:,}'.format(abs(compare_revenue_today_lastday_num)).replace('.', '/').replace(',', '.').replace('/',',')
            if compare_revenue_today_lastday_num >= 0:
                compare_revenue_today_lastday = '(↗ {}%)'.format(compare_revenue_today_lastday_num_format)
            else:
                compare_revenue_today_lastday = '(↘ {}%)'.format(compare_revenue_today_lastday_num_format)

        current_day_temp_revenue = self.format_money(current_day_temp_revenue, u' Triệu')
        last_day_temp_revenue = self.format_money(last_day_temp_revenue, u' Triệu')
        current_month_temp_revenue = self.format_money(current_month_temp_revenue, u' Triệu')
        current_years_temp_revenue = self.format_money(current_years_temp_revenue, u' Triệu')

        user_companys = self.get_user_companys()

        cash_book, debt = self.get_text_block_list()

        current_day = self.get_current_day_info()

        revenue = self.get_product_revenue_cost_period(
            type='revenue', period='week')

        cost = self.get_product_revenue_cost_period(
            type='cost', period='week')

        over_percent_revenue = self.over_percent_revenue_cost(type='revenue', period='week')
        over_percent_cost = self.over_percent_revenue_cost(type='cost', period='week')

        customer = self.get_customer_number()

        employee, inventory, num_invoice, goods_receipt, goods_issue = \
            self.get_employee_inventory_cost_num_invoice()

        top_current_day_customer = \
            self.top_current_day_customer()
        top_revenue_customer = \
            self.top_revenue_customer()

        stock_location_list = self.get_stock_location_list()

        datas = {
            'user_companys': user_companys,
            'cash_book': cash_book,
            'debt': debt,
            'current_day_temp_revenue': current_day_temp_revenue,
            'last_day_temp_revenue': last_day_temp_revenue,
            'compare_revenue_today_lastday': compare_revenue_today_lastday,
            'current_month_temp_revenue': current_month_temp_revenue,
            'current_years_temp_revenue': current_years_temp_revenue,
            'compare_revenue': compare_revenue,
            'current_day': current_day,
            'revenue': revenue,
            'cost': cost,
            'over_percent_revenue': over_percent_revenue,
            'over_percent_cost': over_percent_cost,
            'type': type, #revenue, cost
            'customer': customer,
            'employee': employee,
            'inventory': inventory,
            'num_invoice': num_invoice,
            'goods_receipt': goods_receipt,
            'goods_issue': goods_issue,
            'top_current_day_customer': top_current_day_customer,
            'top_revenue_customer': top_revenue_customer,
            'stock_location_list': stock_location_list,
        }
        return datas

    def get_color(self, index):
        color_list = ['#3E4AAE',
                      '#008EFB',
                      '#F7B112',
                      '#2EBC61',
                      '#FF145B',
                      '#26176B',
                      '#BAD4E6',
                      '#9658FF',
                      ]
        len_list = len(color_list)
        color = color_list[index%len_list]
        return color

    @api.model
    def set_user_company(self, company_id):
        company_ids = self.env.user.company_ids._ids

        if company_id not in company_ids:
            return False

        self.env.user.write({'company_id': company_id})
        return True

    @api.model
    def get_user_companys(self):
        companys = self.env.user.company_ids.name_get()
        company_id = self.env.user.company_id.id
        return {
            'companys': companys,
            'company_id': company_id,
        }


    def get_stock_location_list(self):
        domain = [('usage', '=', 'internal')]
        stocks = self.env['stock.location'].search(domain)
        return [{'name': stock.name, 'id': stock.id} for stock in stocks]

    def get_from_date_to_date(
            self, period='week',
            current_day=datetime.datetime.now().strftime('%Y-%m-%d')):
        current_day = datetime.datetime.strptime(
            current_day,
            '%Y-%m-%d'
        )

        if period == 'week':
            current_weekday = current_day.weekday()
            first_day_of_week = \
                current_day + \
                datetime.timedelta(days=-current_weekday)
            # current_weekday = current_weekday or 7
            return first_day_of_week.strftime(
                '%Y-%m-%d'), current_day.strftime(
                '%Y-%m-%d'), current_weekday

        if period == 'month':
            first_day_of_month = \
                '{}-{}-1'.format(
                    current_day.year,
                    current_day.month
                )
            current_week = current_day.day / 7.0
            round_current_week = int(current_week)
            if round_current_week < current_week:
                round_current_week += 1
            return first_day_of_month, current_day.strftime(
                '%Y-%m-%d'), round_current_week

        # quarter
        if period == 'quarter':
            current_month = current_day.month
            current_quarter = current_month / 3.0
            round_current_quarter = int(current_quarter)
            if round_current_quarter < current_quarter:
                round_current_quarter += 1

            first_month_quarter = round_current_quarter * 3 - 2

            first_day_of_quarter = \
                '{}-{}-01'.format(
                    current_day.year,
                    first_month_quarter
                )
            return first_day_of_quarter, current_day.strftime(
                '%Y-%m-%d'), current_month

        # last_week
        if period == 'last_week':
            current_weekday = current_day.weekday()
            first_day_of_last_week = current_day + datetime.timedelta(days=-current_weekday - 7)
            last_day_of_last_week = current_day + datetime.timedelta(days=-current_weekday - 1)
            return first_day_of_last_week.strftime('%Y-%m-%d'), last_day_of_last_week.strftime('%Y-%m-%d'), current_weekday

        # last month
        if period == 'last_month':
            first_day_of_month = '{}-{}-1'.format(current_day.year, current_day.month)
            first_day_of_month = datetime.datetime.strptime(first_day_of_month, '%Y-%m-%d')
            last_day_of_last_month = first_day_of_month + datetime.timedelta(days=-1)
            first_day_of_last_month = '{}-{}-1'.format(last_day_of_last_month.year, last_day_of_last_month.month)

            return first_day_of_last_month, last_day_of_last_month.strftime(
                '%Y-%m-%d'), first_day_of_month

        # last quarter
        if period == 'last_quarter':
            current_month = current_day.month
            current_quarter = current_month / 3.0
            round_current_quarter = int(current_quarter)
            if round_current_quarter < current_quarter:
                round_current_quarter += 1

            first_month_quarter = round_current_quarter * 3 - 2
            first_day_of_quarter = '{}-{}-01'.format(current_day.year, first_month_quarter)
            first_day_of_quarter = datetime.datetime.strptime(first_day_of_quarter, '%Y-%m-%d')
            last_day_of_last_quarter = first_day_of_quarter + datetime.timedelta(days=-1)

            last_month_of_last_quarter = last_day_of_last_quarter.month
            last_quarter = last_month_of_last_quarter / 3.0
            round_last_quarter = int(last_quarter)
            if round_last_quarter < last_quarter:
                round_last_quarter += 1

            first_month_last_quarter = round_last_quarter * 3 - 2
            first_day_of_last_quarter = \
                '{}-{}-01'.format(
                    last_day_of_last_quarter.year,
                    first_month_last_quarter
                )
            return first_day_of_last_quarter, last_day_of_last_quarter.strftime(
                '%Y-%m-%d'), current_month

        # year
        current_year = current_day.year
        first_day_of_year = \
            '{}-01-01'.format(current_year)
        current_month = current_day.month
        current_quarter = current_month / 3.0
        round_current_quarter = int(current_quarter)
        if round_current_quarter < current_quarter:
            round_current_quarter += 1
        return first_day_of_year, current_day.strftime(
            '%Y-%m-%d'), round_current_quarter

    def get_revenue_data(self, type='revenue', period='week'):
        cr = self.env.cr

        extend_id_dict = {
            'revenue': 'account.data_account_type_revenue',
            'cost': 'account.data_account_type_expenses',
        }

        account_type_id = self.env.ref(
            extend_id_dict.get(type, ''))

        from_date, to_date, current_period = \
            self.get_from_date_to_date(period)

        with_clause = """
            with d as (
                select am.date,
                  sum(ml.credit - ml.debit) as balance
                from account_move_line as ml
                left join account_account as aa
                  on aa.id = ml.account_id
                left join account_move as am
                  on am.id = ml.move_id
                where
                  am.state = 'posted'
                  and am.company_id = {}
                  and aa.user_type_id = {}
                  and am.date >= '{}'
                  and am.date <= '{}'
                group by am.date)
                """.format(self.env.user.company_id.id,
                           account_type_id.id,
                           from_date, to_date)

        labels = []
        data = []

        if period == 'week':
            querry = """{}
                select extract(dow from d.date), balance
                from d""".format(with_clause)
            cr.execute(querry)

            dow_value_dict = \
                dict((row[0], row[1]) for row in cr.fetchall())

            dow_dict = {
                1: u'Thứ 2',
                2: u'Thứ 3',
                3: u'Thứ 4',
                4: u'Thứ 5',
                5: u'Thứ 6',
                6: u'Thứ 7',
                7: 'CN',
            }

            for i in range(1, current_period + 2):
                labels.append(dow_dict.get(i, ''))
                data.append(dow_value_dict.get(i, 0))

            return labels, data

        if period == 'month':
            querry = """
                {}
                select d.date,
                    extract(day from  d.date)/7.0,
                    sum(d.balance)
                from d
                group by d.date
                    """.format(with_clause)
            cr.execute(querry)

            data_dict = {}
            for row in cr.fetchall():
                week = int(row[1])
                if week < row[1]:
                    week += 1
                count = row[2]

                if not data_dict.get(week):
                    data_dict[week] = 0

                data_dict[week] += count

            for week in range(1, current_period + 1):
                labels.append(u'Tuần {}'.format(week))
                data.append(data_dict.get(week, 0))
            return labels, data
        # quarter
        if period == 'quarter':
            querry = """
                {}
                select extract(month from d.date) as month,
                    sum(d.balance)
                from d
                group by extract(month from  d.date)
                    """.format(with_clause)

            cr.execute(querry)
            query_result_dict = \
                dict((row[0], row[1]) for row in cr.fetchall())

            current_month = current_period
            current_quarter = current_month / 3.0
            round_current_quarter = int(current_quarter)
            if round_current_quarter < current_quarter:
                round_current_quarter += 1

            first_month_quarter = round_current_quarter * 3 - 2

            for month in range(
                    first_month_quarter,
                            current_period + 1):
                labels.append(u'Tháng {}'.format(month))
                data.append(query_result_dict.get(month, 0))

            return labels, data

            #     year
        querry = """
                    {}
                    select extract(month from d.date)/3.0 as quarter,
                        sum(d.balance)
                    from d
                    group by extract(month from  d.date)
                """.format(with_clause)
        cr.execute(querry)
        query_result_dict = {}
        for row in cr.fetchall():
            quarter = row[0]
            round_quarter = int(quarter)
            if round_quarter < quarter:
                round_quarter += 1

            balance = row[1] or 0

            if not query_result_dict.get(round_quarter, 0):
                query_result_dict[round_quarter] = 0

            query_result_dict[round_quarter] += balance

        current_quarter = current_period

        for quarter in range(1, current_quarter + 1):
            labels.append(u'Quý {}'.format(quarter))
            data.append(query_result_dict.get(quarter, 0))

        return labels, data

    def get_revenue_area_chart_datas(
            self, type='revenue', period='week', **kw):
        # print '----------revenue'
        # print type
        # print period

        labels, datas = self.get_revenue_data(type, period)

        label = u"Doanh thu"
        if type == 'cost':
            label = u"Chi phí"

        data = {
            'labels': labels,
            'datasets': [{
                'data': datas,
                'label': label,
                'borderColor': "#0099E5",
                'fill': False
            }
            ]
        }
        return data

    def get_customer_multi_line_chart_datas_week(self, **kw):
        cr = self.env.cr

        labels = []
        category_dict = {}

        from_date, to_date, current = \
            self.get_from_date_to_date()

        query = """
                    select c.id as id,
                      c.name as name,
                      a.create_date::date as create_date,
                      count(*) as count_partner
                    from fleet_repair a
                      left join res_partner as rp
                      on rp.id = a.client_id
                      left join res_partner_res_partner_category_rel as rel
                      on rp.id=rel.partner_id
                      left join res_partner_category as c
                      on c.id=rel.category_id
                    where a.state != 'cancel'
                      and a.company_id = {}
                      and a.create_date::date >= '{}'
                      and a.create_date::date <= '{}'
                    group by c.id, c.name,
                      a.create_date::date
                    """.format(
            self.env.user.company_id.id,
            from_date,
            to_date
        )
        cr.execute(query)

        for row in cr.dictfetchall():
            id = row['id'] or 0
            name = row['name'] or u'Không xác định'
            dow = datetime.datetime.strptime(
                row['create_date'], '%Y-%m-%d').weekday()
            count_partner = row['count_partner']

            if not category_dict.get((id, name), False):
                category_dict[(id, name)] = {}

            if not category_dict[(id, name)].get(dow, False):
                category_dict[(id, name)][dow] = 0

                category_dict[(id, name)][dow] += count_partner

        dow_dict = {
            0: u'Thứ 2',
            1: u'Thứ 3',
            2: u'Thứ 4',
            3: u'Thứ 5',
            4: u'Thứ 6',
            5: u'Thứ 7',
            6: 'CN',
        }

        dow_category_dict = {}

        for i in range(0, current + 1):
            labels.append(dow_dict.get(i, ''))
            for categ_id in category_dict.keys():
                if not dow_category_dict.get(categ_id, False):
                    dow_category_dict[categ_id] = []
                dow_category_dict[categ_id].append(
                    category_dict[categ_id].get(i, 0))

        return labels, dow_category_dict

    def get_customer_multi_line_chart_datas_month(self):
        cr = self.env.cr
        labels = []
        category_dict = {}

        current_day = datetime.datetime.now()

        first_day_of_month = \
            '{}-{}-1'.format(
                current_day.year,
                current_day.month
            )
        query = """
                    select c.id, c.name,
                      a.create_date::date,
                      extract(day from  a.create_date::date)/7.0,
                      count(*)
                    from fleet_repair a
                      left join res_partner as rp
                      on rp.id = a.client_id
                      left join res_partner_res_partner_category_rel as rel
                      on rp.id=rel.partner_id
                      left join res_partner_category as c
                      on c.id=rel.category_id
                    where a.state != 'cancel'
                      and a.company_id = {}
                      and a.create_date::date >= '{}'
                      and a.create_date::date <= '{}'
                    group by c.id, c.name, a.create_date::date
                """.format(
            self.env.user.company_id.id,
            first_day_of_month,
            current_day.strftime('%Y-%m-%d')
        )
        cr.execute(query)

        data_dict = {}
        for row in cr.fetchall():
            categ_id = row[0] or 0
            categ_name = row[1] or u'Không xác định'
            week = int(row[3])
            if week < row[3]:
                week += 1
            count = row[4]

            if not data_dict.get((categ_id, categ_name)):
                data_dict[(categ_id, categ_name)] = {}

            data_dict[(categ_id, categ_name)][week] = count

        current_week = current_day.day / 7.0
        round_current_week = int(current_week)
        if round_current_week < current_week:
            round_current_week += 1

        for week in range(1, round_current_week + 1):
            labels.append(u'Tuần {}'.format(week))
            for categ in data_dict.keys():
                count = data_dict[categ].get(week, 0)

                if not category_dict.get(categ, False):
                    category_dict[categ] = []
                category_dict[categ].append(count)
        return labels, category_dict

    def get_customer_multi_line_chart_datas_quarter(self):
        cr = self.env.cr
        labels = []
        category_dict = {}

        current_day = datetime.datetime.now()

        current_month = current_day.month
        current_quarter = current_month / 3.0
        round_current_quarter = int(current_quarter)
        if round_current_quarter < current_quarter:
            round_current_quarter += 1

        first_month_quarter = round_current_quarter * 3 - 2

        first_day_of_quarter = \
            '{}-{}-01'.format(
                current_day.year,
                first_month_quarter
            )
        query = """
                    select c.id, c.name,
                      extract(month from a.create_date::date) as month,
                      count(*) as c
                    from fleet_repair a
                      left join res_partner as rp
                      on rp.id = a.client_id
                      left join res_partner_res_partner_category_rel as rel
                      on rp.id=rel.partner_id
                      left join res_partner_category as c
                      on c.id=rel.category_id
                    where a.state != 'cancel'
                      and a.company_id = {}
                      and a.create_date::date >= '{}'
                      and a.create_date::date <= '{}'
                    group by c.id, c.name,
                      extract(month from  a.create_date::date)
                """.format(
            self.env.user.company_id.id,
            first_day_of_quarter,
            current_day.strftime('%Y-%m-%d')
        )
        cr.execute(query)
        data_dict = {}
        for row in cr.dictfetchall():
            categ_id = row['id'] or 0
            categ_name = row['name'] or u'Không xác định'
            month = row['month']
            count = row['c']
            if not data_dict.get((categ_id,categ_name), False):
                data_dict[(categ_id, categ_name)] = {}

            data_dict[(categ_id, categ_name)][month] = count

        for month in range(
                first_month_quarter,
                        current_month + 1):
            labels.append(u'Tháng {}'.format(month))
            for categ in data_dict.keys():
                if not category_dict.get(categ, False):
                    category_dict[categ] = []

                category_dict[categ].append(
                    data_dict[categ].get(month, 0))

        return labels, category_dict

    def get_customer_multi_line_chart_datas(self, period='week', **kw):
        period_dict = {
            'week': self.get_customer_multi_line_chart_datas_week,
            'month': self.get_customer_multi_line_chart_datas_month,
            'quarter': self.get_customer_multi_line_chart_datas_quarter,
        }
        labels, category_dict = period_dict[period]()

        datasets = []
        index = 0
        for categ in category_dict:
            color = self.get_color(index)
            datasets.append({
                'data': category_dict[categ],
                'label': categ[1],
                'borderColor': color,
                'fill': True
            })
            index += 1

        datas = {
            'labels': labels,
            'datasets': datasets
        }

        return datas

    def get_car_in_area_chart_datas(self, period='week', **kw):
        # print '----------car_in'
        # print period

        cr = self.env.cr

        labels = []
        data = []

        current_day = datetime.datetime.now()

        if period == 'week':
            current_weekday = current_day.weekday() or 7
            first_day_of_week = \
                current_day + \
                datetime.timedelta(days=-current_day.weekday())

            query = """
                    select a.create_date::date,
                      extract(dow from  a.create_date::date),
                      count(*)
                    from fleet_repair a
                    where a.state != 'cancel'
                      and a.company_id = {}
                      and a.create_date::date >= '{}'
                      and a.create_date::date <= '{}'
                    group by a.create_date::date
                    """.format(
                self.env.user.company_id.id,
                first_day_of_week.strftime('%Y-%m-%d'),
                current_day.strftime('%Y-%m-%d')
            )
            cr.execute(query)

            dow_value_dict = \
                dict((row[1], row[2]) for row in cr.fetchall())

            dow_dict = {
                1: u'Thứ 2',
                2: u'Thứ 3',
                3: u'Thứ 4',
                4: u'Thứ 5',
                5: u'Thứ 6',
                6: u'Thứ 7',
                7: 'CN',
            }

            for i in range(1, current_weekday + 2):
                labels.append(dow_dict.get(i, ''))
                data.append(dow_value_dict.get(i, 0))

        if period == 'month':
            first_day_of_month = \
                '{}-{}-1'.format(
                    current_day.year,
                    current_day.month
                )
            query = """
                        select a.create_date::date,
                          extract(day from  a.create_date::date)/7.0,
                          count(*)
                        from fleet_repair a
                        where a.state != 'cancel'
                          and a.company_id = {}
                          and a.create_date::date >= '{}'
                          and a.create_date::date <= '{}'
                        group by a.create_date::date
                    """.format(
                self.env.user.company_id.id,
                first_day_of_month,
                current_day.strftime('%Y-%m-%d')
            )
            cr.execute(query)
            data_dict = {}
            for row in cr.fetchall():
                week = int(row[1])
                if week < row[1]:
                    week += 1
                count = row[2]

                if not data_dict.get(week):
                    data_dict[week] = 0

                data_dict[week] += count

            current_week = current_day.day / 7.0
            round_current_week = int(current_week)
            if round_current_week < current_week:
                round_current_week += 1

            for week in range(1, round_current_week + 1):
                labels.append(u'Tuần {}'.format(week))
                data.append(data_dict.get(week, 0))

        if period == 'quarter':
            current_month = current_day.month
            current_quarter = current_month / 3.0
            round_current_quarter = int(current_quarter)
            if round_current_quarter < current_quarter:
                round_current_quarter += 1

            first_month_quarter = round_current_quarter * 3 - 2

            first_day_of_quarter = \
                '{}-{}-01'.format(
                    current_day.year,
                    first_month_quarter
                )
            query = """
                        select extract(month from a.create_date::date) as month,
                          count(*)
                        from fleet_repair a
                        where a.state != 'cancel'
                          and a.company_id = {}
                          and a.create_date::date >= '{}'
                          and a.create_date::date <= '{}'
                        group by extract(month from  a.create_date::date)
                    """.format(
                self.env.user.company_id.id,
                first_day_of_quarter,
                current_day.strftime('%Y-%m-%d')
            )
            cr.execute(query)
            query_result_dict = \
                dict((row[0], row[1]) for row in cr.fetchall())

            for month in range(
                    first_month_quarter,
                            current_month + 1):
                labels.append(u'Tháng {}'.format(month))
                data.append(query_result_dict.get(month, 0))

        total = sum(data) or 0

        datas = {
            'labels': labels,
            'datasets': [{
                'data': data,
                'total': sum(data),
                'percent': total and sum(data)/total or 0,
                'label': u"Xe đến",
                'borderColor': "#3e95cd",
                'fill': False
            }
            ]
        }
        return datas

    def get_car_in_pie_chart_datas(self, **kw):
        query = """
                with d as (
                    select fvmb.id,
                      fvmb.name,
                      count(fr.id) as c
                    from fleet_repair as fr
                      left join fleet_repair_fleet_vehicle_rel as rel
                      on rel.fleet_repair_id = fr.id
                      left join fleet_vehicle as fv
                      on fv.id = rel.fleet_vehicle_id
                      left join fleet_vehicle_model as fvm
                      on fv.model_id = fvm.id
                      left join fleet_vehicle_model_brand as fvmb
                      on fvmb.id = fvm.brand_id
                    where fr.state != 'cancel'
                      and fr.company_id = %s
                    group by fvmb.id, fvmb.name
                )
                select id, name, c from d
                order by c desc
                """
        self.env.cr.execute(query, [self.env.user.company_id.id])
        labels = []
        data = []
        colors = []
        total = 0
        index = 0
        other = 0
        for row in self.env.cr.dictfetchall():
            label = row['name'] or u'Không xác định'
            count = row['c'] or 0
            total += count

            if index < 5:
                labels.append(label)
                data.append(count)
                colors.append(self.get_color(index))
                index += 1
                continue

            other += count
        labels.append('Other')
        data.append(other)
        colors.append(self.get_color(index))

        data = {
            'labels': labels,
            'datasets': [
                {
                    'label': "Top model",
                    'data': data,
                    'backgroundColor': colors,
                    'borderColor': colors,
                    'borderWidth': [1 for d in data]
                }
            ],
            'inside_text': str(total),
        }
        return data

    def get_top10_service_package_rate_data(self, period='week', **kw):
        revenue_account_type_id = \
            self.env.ref('account.data_account_type_revenue').id

        from_date, to_date, current = \
            self.get_from_date_to_date(period)

        query = """
                    with d as (
                    select pt.id,
                        pt.name,
                        sum(ml.credit - ml.debit) as balance
                    from product_template as pt
                        left join product_product as pp
                        on pp.product_tmpl_id = pt.id
                        left join account_move_line as ml
                        on ml.product_id = pp.id
                        left join account_account as aa
                        on aa.id = ml.account_id
                        left join account_move as am
                        on am.id = ml.move_id
                    where pt.is_service_package is true
                        and am.company_id = {company_id}
                        and aa.user_type_id = {account_type_id}
                        and am.state = 'posted'
                        and am.date >= '{from_date}'
                        and am.date <= '{to_date}'
                    group by pt.id,
                        pt.name
                    )
                    select id, name, balance
                    from d
                    order by balance desc
                """.format(company_id=self.env.user.company_id.id,
                           account_type_id=revenue_account_type_id,
                           from_date=from_date,
                           to_date=to_date)
        self.env.cr.execute(query)
        labels = []
        colors = []
        data = []
        index = -1
        total = 0
        other = 0
        for row in self.env.cr.dictfetchall():
            name = row['name']
            balance = row['balance']
            total += balance
            index += 1

            if index > 10:
                other += balance
                continue

            labels.append(name)
            data.append(balance)
            color = self.get_color(index)
            colors.append(color)

        total = self.format_money(total, u'triệu')

        if other:
            color = self.get_color(11)
            labels.append(_('Other'))
            data.append(other)
            colors.append(color)

        datas = {
            'labels': labels,
            'datasets': [
                {
                    'label': "Product Service",
                    'data': data,
                    'backgroundColor': colors,
                    'borderColor': colors,
                    'borderWidth': [1 for d in data]
                }
            ],
            'inside_text': total,
        }
        return datas

    def get_car_in_multi_line_chart_datas(self, period='week', **kw):
        cr = self.env.cr

        labels = []
        category_dict = {}

        current_day = datetime.datetime.now()

        if period == 'week':
            current_weekday = current_day.weekday() or 7
            first_day_of_week = \
                current_day + \
                datetime.timedelta(days=-current_weekday)

            query = """
                        select c.id as id,
                          c.name as name,
                          a.create_date::date as create_date,
                          extract(dow from  a.create_date::date) as dow,
                          count(*) as count_partner
                        from fleet_repair a
                          left join res_partner as rp
                          on rp.id = a.client_id
                          left join res_partner_res_partner_category_rel as rel
                          on rp.id=rel.partner_id
                          left join res_partner_category as c
                          on c.id=rel.category_id
                        where a.state != 'cancel'
                          and a.company_id = {}
                          and a.create_date::date >= '{}'
                          and a.create_date::date <= '{}'
                        group by c.id, c.name,
                          a.create_date::date
                        """.format(
                self.env.user.company_id.id,
                first_day_of_week.strftime('%Y-%m-%d'),
                current_day.strftime('%Y-%m-%d')
            )
            cr.execute(query)


            for row in cr.dictfetchall():
                id = row['id']
                name = row['name']
                dow = row['dow']
                count_partner = row['count_partner']

                if not category_dict.get(id, False):
                    category_dict[(id,name)] = {}
                category_dict[(id,name)][dow] = count_partner

            dow_dict = {
                1: u'Thứ 2',
                2: u'Thứ 3',
                3: u'Thứ 4',
                4: u'Thứ 5',
                5: u'Thứ 6',
                6: u'Thứ 7',
                7: 'CN',
            }

            dow_category_dict = {}

            for i in range(1, current_weekday + 2):
                labels.append(dow_dict.get(i, ''))
                for categ_id in category_dict.keys():
                    if not dow_category_dict.get(categ_id, False):
                        dow_category_dict[categ_id] = []
                    dow_category_dict[categ_id].append(
                        category_dict[categ_id].get(i, 0))

        if period == 'month':
            first_day_of_month = \
                '{}-{}-1'.format(
                    current_day.year,
                    current_day.month
                )
            query = """
                        select a.create_date::date,
                          extract(day from  a.create_date::date)/7.0,
                          count(*)
                        from fleet_repair a
                        where a.state != 'cancel'
                          and a.company_id = {}
                          and a.create_date::date >= '{}'
                          and a.create_date::date <= '{}'
                        group by a.create_date::date
                    """.format(
                self.env.user.company_id.id,
                first_day_of_month,
                current_day.strftime('%Y-%m-%d')
            )
            cr.execute(query)
            data_dict = {}
            for row in cr.fetchall():
                week = int(row[1])
                if week < row[1]:
                    week += 1
                count = row[2]

                if not data_dict.get(week):
                    data_dict[week] = 0

                data_dict[week] += count

            current_week = current_day.day / 7.0
            round_current_week = int(current_week)
            if round_current_week < current_week:
                round_current_week += 1

            for week in range(1, round_current_week + 1):
                labels.append(u'Tuần {}'.format(week))
                # data.append(data_dict.get(week, 0))

        if period == 'quarter':
            current_month = current_day.month
            current_quarter = current_month / 3.0
            round_current_quarter = int(current_quarter)
            if round_current_quarter < current_quarter:
                round_current_quarter += 1

            first_month_quarter = round_current_quarter * 3 - 2

            first_day_of_quarter = \
                '{}-{}-01'.format(
                    current_day.year,
                    first_month_quarter
                )
            query = """
                                select extract(month from a.create_date::date) as month,
                                  count(*)
                                from fleet_repair a
                                where a.state != 'cancel'
                                  and a.company_id = {}
                                  and a.create_date::date >= '{}'
                                  and a.create_date::date <= '{}'
                                group by extract(month from  a.create_date::date)
                            """.format(
                self.env.user.company_id.id,
                first_day_of_quarter,
                current_day.strftime('%Y-%m-%d')
            )
            cr.execute(query)
            query_result_dict = \
                dict((row[0], row[1]) for row in cr.fetchall())

            for month in range(
                    first_month_quarter,
                            current_month + 1):
                labels.append(u'Tháng {}'.format(month))
                # data.append(query_result_dict.get(month, 0))

        # labels = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN']
        # data1 = [20, 30, 50, 21, 18, 9, 11]
        # data2 = [5, 15, 12, 32, 11, 18, 40]
        # data3 = [11, 44, 23, 22, 19, 14, 12]

        datasets = []
        for categ in category_dict:
            datasets.append({
                'data': category_dict[categ],
                'label': categ[1],
                'borderColor': "#3e95cd",
                'fill': True
            })

        datas = {
            'labels': labels,
            'datasets': datasets
        }

        return datas

    def get_revenue_cost_product_type_pie_chart(self, type, period):
        cr = self.env.cr

        extend_id_dict = {
            'revenue': 'account.data_account_type_revenue',
            'cost': 'account.data_account_type_expenses',
        }

        account_type = self.env.ref(
            extend_id_dict.get(type, ''))

        from_date, to_date, current_period = \
            self.get_from_date_to_date(period)

        querry = """
                select
                  pt.type, sum(ml.credit - ml.debit) as balance
                from account_move_line as ml
                left join account_account as aa
                  on aa.id = ml.account_id
                left join account_move as am
                  on am.id = ml.move_id
                left join product_product as pp
                  on pp.id = ml.product_id
                left join product_template as pt
                  on pt.id = pp.product_tmpl_id
                where
                  am.state = 'posted'
                  and aa.user_type_id = {}
                  and am.company_id = {}
                  and am.date >= '{}'
                  and am.date <= '{}'
                group by pt.type
                """.format(account_type.id,
                           self.env.user.company_id.id,
                           from_date, to_date)

        cr.execute(querry)
        label_dict = {
            'revenue': u'Doanh thu',
            'cost': u'Chi phí',
        }
        product = 0
        service = 0
        other = 0
        for row in self.env.cr.fetchall():
            product_type = row[0]
            balance = row[1] or 0
            if product_type in ('product', 'consu'):
                product += balance
            elif product_type == 'service':
                service += balance
            else:
                other += balance

        datas = {
            'labels': [u"Sản phẩm", u"Dịch vụ",
                       u"{} khác".format(label_dict.get(type, ''))],
            'datasets': [
                {
                    'label': "Product Service",
                    'data': [product, service, other],
                    'backgroundColor': [self.get_color(index) for index in range(0,3)],
                    'borderColor': [self.get_color(index) for index in range(0,3)],
                    'borderWidth': [1, 1, 1]
                }
            ],
            'inside_text': '',
        }
        return datas

    def get_product_revenue_cost_period(
            self, type, period):
        cr = self.env.cr

        extend_id_dict = {
            'revenue': 'account.data_account_type_revenue',
            'cost': 'account.data_account_type_expenses',
        }

        account_type = self.env.ref(
            extend_id_dict.get(type, ''))

        from_date, to_date, current_period = \
            self.get_from_date_to_date(period)

        querry = """
                    select
                      sum(ml.credit - ml.debit) as balance
                    from account_move_line as ml
                    left join account_account as aa
                      on aa.id = ml.account_id
                    left join account_move as am
                      on am.id = ml.move_id
                    left join product_product as pp
                      on pp.id = ml.product_id
                    left join product_template as pt
                      on pt.id = pp.product_tmpl_id
                    where
                      am.state = 'posted'
                      and aa.user_type_id = {}
                      and am.company_id = {}
                      and am.date >= '{}'
                      and am.date <= '{}'
                    """.format(account_type.id,
                               self.env.user.company_id.id,
                               from_date, to_date)

        cr.execute(querry)
        querry_result = cr.fetchone()
        period_value = querry_result and querry_result[0] or 0
        period_value_num = period_value
        period_value = self.format_money(period_value)

        current_year = datetime.datetime.now().year
        last_year = current_year - 1
        querry = """
                    select
                      sum(ml.credit - ml.debit) as balance
                    from account_move_line as ml
                    left join account_account as aa
                      on aa.id = ml.account_id
                    left join account_move as am
                      on am.id = ml.move_id
                    left join product_product as pp
                      on pp.id = ml.product_id
                    left join product_template as pt
                      on pt.id = pp.product_tmpl_id
                    where
                      am.state = 'posted'
                      and aa.user_type_id = {}
                      and extract(year from  am.date) = {}
                      and am.company_id = {}
                """
        last_year_querry = \
            querry.format(account_type.id,
                          last_year,
                          self.env.user.company_id.id)
        cr.execute(last_year_querry)
        querry_result = cr.fetchone()
        last_year_revenue = querry_result and querry_result[0] or 0

        current_year_querry = \
            querry.format(account_type.id,
                          current_year,
                          self.env.user.company_id.id)

        cr.execute(current_year_querry)
        querry_result = cr.fetchone()
        current_year_revenue = querry_result and querry_result[0] or 0

        over_total = current_year_revenue - last_year_revenue
        over_percent = ''
        if not last_year_revenue:
            if not current_year_revenue:
                over_percent = '↗ 0%'
            else:
                over_percent = '↗'
        else:
            over_percent_num = over_total * 100.0 / last_year_revenue
            over_percent_num = float("{0:.1f}".format(over_percent_num))
            over_percent_num_format = '{:,}'.format(abs(over_percent_num)).replace('.', '/').replace(',', '.').replace('/', ',')

            if over_percent_num >= 0:
                over_percent = '↗ {}%'.format(over_percent_num_format)
            else:
                over_percent = '↘ {}%'.format(over_percent_num_format)

        current_year_revenue = self.format_money(current_year_revenue)
        last_year_revenue = self.format_money(last_year_revenue)
        over_total = self.format_money(over_total)

        data = {
            'last_year_revenue': last_year_revenue,
            'current_year_revenue': current_year_revenue,
            'over_percent': over_percent,
            'over_total': over_total,
            'type': 'week',  # month, quarter
            'period_value': period_value,
            'period_value_num': period_value_num,
        }

        return data

    def product_revenue_cost_period(self, type, period, product_type,
                                    **kw):
        data = self.get_product_revenue_cost_period(
            type, period)

        return data

    def get_balance(self, account_code):
        cr = self.env.cr

        querry = """
                    select sum(ml.debit) - sum(ml.credit)
                    from account_move_line as ml
                      left join account_account as aa
                      on aa.id = ml.account_id
                      left join account_move as am
                      on am.id = ml.move_id
                    where
                      am.state = 'posted'
                      and aa.code like '{}%'
                      and ml.company_id = {}
                """.format(account_code, self.env.user.company_id.id)
        cr.execute(querry)
        querry_result = cr.fetchone()
        balance = querry_result and querry_result[0] or 0
        return balance

    def format_money(self, num, unit=''):
        unit = u' đ'
        divisor = 1
        if abs(num) >= 1000000.0:
            unit = u' triệu'
            divisor = 1000000.0
        if abs(num) >= 1000000000.0:
            unit = u' tỷ'
            divisor = 1000000000.0

        num = round(num / divisor, 1)
        num_text = '{:,}'.format(num).replace(
            '.', '/').replace(',', '.').replace('/', ',') + unit
        return num_text

    def get_text_block_list(self):
        # account_move_line_obj = \
        #     http.request.env['account.move.line']

        unit = u' triệu'

        cash = self.get_balance('111')
        cash_text = self.format_money(cash, unit)

        bank = self.get_balance('112')
        bank_text = self.format_money(bank, unit)

        cash_book = cash + bank
        cash_book_text = self.format_money(cash_book, unit).upper()

        supplier = -self.get_balance('331')
        supplier_text = self.format_money(supplier, unit)

        customer = self.get_balance('131')
        customer_text = self.format_money(customer, unit)

        debt = customer - supplier
        debt_text = self.format_money(debt, unit).upper()

        cash_book_block = {
                'title': {
                    'label': u'SỔ QUỸ',
                    'value': cash_book_text
                },
                'item': [
                    {'label': u'Tiền mặt',
                     'value': cash_text},
                    {'label': u'Ngân hàng',
                     'value': bank_text},
                ],
                'class': 'text-block-left',
            }
        debt_block = {
                'title': {
                    'label': u'CÔNG NỢ',
                    'value': debt_text
                },
                'item': [
                    {'label': u'Nhà cung cấp',
                     'value': supplier_text},
                    {'label': u'Khách hàng',
                     'value': customer_text},
                ],
                'class': 'text-block-right',
            }
        return cash_book_block, debt_block

    def get_product_service_rate_data(self, period='week', **kw):
        from_date, to_date, current = \
            self.get_from_date_to_date(period)

        revenue_account_type_id = \
            self.env.ref('account.data_account_type_revenue').id

        querry = """
                    select
                        pt.type,
                        sum(ml.credit - ml.debit) as balance

                    from account_move_line as ml
                      left join account_move as am
                        on am.id = ml.move_id
                      left join account_account as aa
                        on aa.id = ml.account_id
                      left join product_product as pp
                        on pp.id = ml.product_id
                      left join product_template as pt
                        on pt.id = pp.product_tmpl_id
                    where aa.user_type_id = {revenue_account_type_id}
                      and am.company_id = {company_id}
                      and am.date >= %s
                      and am.date <= %s
                      and am.state = 'posted'
                    group by pt.type
                """.format(
            company_id=self.env.user.company_id.id,
            revenue_account_type_id=revenue_account_type_id)

        self.env.cr.execute(querry, [from_date, to_date])

        product = 0
        service = 0

        for row in self.env.cr.fetchall():
            revenue = row[1] or 0
            if row[0] in ('consu', 'product'):
                product += revenue

            elif row[0] == 'service':
                service += revenue

        datas = {
            'labels': [u"Sản phẩm", u"Dịch vụ"],
            'datasets': [
                {
                    'label': "Product Service",
                    'data': [product, service],
                    'backgroundColor': [
                        "#DEB887",
                        "#A9A9A9"
                    ],
                    'borderColor': [
                        "#CDA776",
                        "#989898"
                    ],
                    'borderWidth': [1, 1]
                }
            ],
            'inside_text': '',
        }
        return datas

    # Khoi doanh thu tam tinh
    def get_temporary_revenue(self, from_time, to_time):
        # cr = self.env.cr
        domain = [('state', 'not in', ('draft', 'sent', 'cancel'))]
        if from_time:
            domain.append(('confirmation_date', '>=', from_time))
        if to_time:
            domain.append(('confirmation_date', '<', to_time))

        sale_orders = self.env['sale.order'].search(domain)
        revenue = 0.0
        for sale_order in sale_orders:
            revenue += sale_order.amount_total_repair
        return revenue


    def get_current_day_info(self):
        cr = self.env.cr
        local_date_now = self.env[
            'change.datetime'].change_utc_to_local_datetime(
            datetime.datetime.strftime(datetime.datetime.now(),
                                       '%Y-%m-%d %H:%M:%S'), '%Y-%m-%d')
        start_time_today = local_date_now + ' 00:00:00'
        start_time_today_utc = self.env[
            'change.datetime'].change_local_datetime_to_utc(start_time_today,
                                                            '%Y-%m-%d %H:%M:%S')
        # fleet_repair_today = self.env['fleet.repair'].search([('create_date', '>=', start_time_today_utc)], count=True)
        car_into_gara_today = self.env['sale.order'].search([('create_date', '>=', start_time_today_utc),
                                                          ('create_form_fleet', '=', True),
                                                          ('state', '!=', 'cancel')], count=True)
        # car_into_gara_today = fleet_repair_today + sale_order_repair_today

        car_out_gara_today = self.env['sale.order'].search([('done_date', '>=', start_time_today_utc),
                                                          ('create_form_fleet', '=', True)], count=True)
        # car_cancel_today = self.env['sale.order'].search([('cancel_date', '>=', start_time_today_utc),
        #                                                   ('create_form_fleet', '=', True)], count=True)
        # car_out_gara_today = car_done_today + car_cancel_today

        # car_in_gara = self.env['fleet.repair'].search([('state', 'not in', ('done', 'cancel'))], count=True) +  \
        #               self.env['sale.order'].search([('fleet_repair_id', '=', False),
        #                                              ('create_form_fleet', '=', True),
        #                                              ('state', 'not in', ('done', 'cancel'))], count=True)

        car_in_gara = self.env['sale.order'].search([('create_form_fleet', '=', True),
                                                     ('state', 'not in', ('done', 'cancel'))], count=True)

        querry = """
                    select count(*)
                    from
                        (
                        select a.*,w.state workingstate, w.id as w_id,
                          (case when c.id is null then 0  else 1 end) vehicle_id
                        from sale_order a
                          left join fleet_vehicle_sale_order_rel m
                            on a.id=m.sale_order_id
                          left join fleet_vehicle c on c.id=m.fleet_vehicle_id
                          left join fleet_repair b on b.sale_order_id=a.id
                          left join fleet_workorder w on w.fleet_repair_id=b.id
                        where a.state in ('sale')
                          and a.company_id = %s
                        ) tb
                      where tb.vehicle_id=1
                      and tb.workingstate in ('draft')
                """
        cr.execute(querry, [self.env.user.company_id.id])
        querry_result = cr.fetchone()
        waiting = querry_result and querry_result[0] or 0

        querry = """
                    select count(*)
                    from (select a.*,w.state workingstate,
                            (case when c.id is null then 0  else 1 end) vehicle_id
                          from sale_order a
                            left join fleet_vehicle_sale_order_rel m
                              on a.id=m.sale_order_id
                            left join fleet_vehicle c
                              on c.id=m.fleet_vehicle_id
                            left join fleet_repair b
                              on b.sale_order_id=a.id
                            left join fleet_workorder w
                              on w.fleet_repair_id=b.id
                            where a.state in ('sale')
                              and a.company_id = %s
                          ) tb
                        where tb.vehicle_id=1
                          and tb.workingstate in ('startworking','pause')
                """
        cr.execute(querry, [self.env.user.company_id.id])
        querry_result = cr.fetchone()
        repairing = querry_result and querry_result[0] or 0

        querry = """
                    select count(w.id)
                    from fleet_workorder as w
                        left join sale_order as o on o.id = w.sale_order_id
                    where w.state = 'done'
                        and w.done_date::date = now()::date
                        and o.state not in ('cancel', 'draft')
                        and w.company_id = %s
                """
        cr.execute(querry, [self.env.user.company_id.id])
        querry_result = cr.fetchone()
        done = querry_result and querry_result[0] or 0

        querry = """
                    select count(*)
                    from
                    (
                        select a.*,
                            (case when a.sale_order_id is null then 0 else 1 end) sale
                        from fleet_repair a
                            left join sale_order b
                            on a.sale_order_id = b.id
                          where a.company_id = %s
                    ) tb
                    where (tb.sale=0 or
                    (tb.sale=1 and tb.confirm_sale_order=false))
                    and date(tb.create_date) = now()::date
                """

        cr.execute(querry, [self.env.user.company_id.id])
        querry_result = cr.fetchone()
        not_order = querry_result and querry_result[0] or 0

        extend_account_type_id = 'account.data_account_type_revenue'

        account_type = self.env.ref(extend_account_type_id)

        querry = """
                    select
                      sum(ml.credit - ml.debit) as balance
                    from account_move_line as ml
                    left join account_account as aa
                      on aa.id = ml.account_id
                    left join account_move as am
                      on am.id = ml.move_id
                    where
                      am.state = 'posted'
                      and aa.user_type_id = %s
                      and am.company_id = %s
                      and am.date = now()::date
                    group by am.date
                """

        cr.execute(querry, [account_type.id, self.env.user.company_id.id])
        querry_result = cr.fetchone()
        current_day_revenue = querry_result and querry_result[0] or 0

        current_day_revenue = round(current_day_revenue / 1000000, 2)
        current_day_revenue_text = '{:,}'.format(
            current_day_revenue).replace(
            '.', '/').replace(',', '.').replace('/', ',')

        current_day = {
            'revenue': current_day_revenue_text,
            'car_into_gara_today': car_into_gara_today,
            'car_out_gara_today': car_out_gara_today,
            'car_in_gara': car_in_gara,
            'repairing': repairing,
            'has_been_repair': done,
            'waiting': waiting,
            'not_order': not_order
        }

        return current_day

    @api.model
    def over_percent_revenue_cost(self, type, period, **kw):
        data = {}
        if period == 'year':
            current_balance = self.get_product_revenue_cost_period(type, 'week')
            data['over_percent'] = current_balance['over_percent']
        else:
            dict_map_period = {
                'week': 'last_week',
                'month': 'last_month',
                'quarter': 'last_quarter'}
            current_balance = self.get_product_revenue_cost_period(type, period)

            last_balance = self.get_product_revenue_cost_period(type, dict_map_period[period])

            over_percent = ''
            if not last_balance['period_value_num']:
                if not current_balance['period_value_num']:
                    over_percent = '(↗ 0%)'
                else:
                    over_percent = '(↗)'
            else:
                over_percent_num = ((current_balance['period_value_num'] - last_balance['period_value_num']) / last_balance['period_value_num']) * 100.0
                over_percent_num = float("{0:.1f}".format(over_percent_num))
                over_percent_num_format = '{:,}'.format(abs(over_percent_num)).replace('.', '/').replace(',', '.').replace('/', ',')

                if over_percent_num >= 0:
                    over_percent = '(↗ {}%)'.format(over_percent_num_format)
                else:
                    over_percent = '(↘ {}%)'.format(over_percent_num_format)
            data['over_percent'] = over_percent

        return data

    def get_customer_number(self):
        cr = self.env.cr

        querry = """
                    select
                        c.id,
                        c.name,
                        count(rp.id)
                    from res_partner rp
                    left join res_partner_res_partner_category_rel rel on rp.id=rel.partner_id
                    left join res_partner_category c on c.id=rel.category_id
                    where rp.customer is true
                        and rp.active is true
                        and rp.parent_id is null
                    group by c.id, c.name
                """
        cr.execute(querry)

        customer = {
            'types': []
        }
        for row in cr.fetchall():
            categ_name = row[1] or u'Không xác định'
            count = row[2]
            customer['types'].append(
                (categ_name, count)
            )

        querry = """
                    select count(rp.id)
                    from res_partner rp
                    where rp.customer is true
                        and rp.active is true
                        and rp.parent_id is null
                """
        cr.execute(querry)
        querry_result = cr.fetchone()
        customer['total'] = querry_result and querry_result[0] or 0

        return customer

    def get_employee_inventory_cost_num_invoice(self):
        cr = self.env.cr
        employee = self.env['hr.employee'].search([], count=True)
        local_date_now = self.env[
            'change.datetime'].change_utc_to_local_datetime(
            datetime.datetime.strftime(datetime.datetime.now(),
                                       '%Y-%m-%d %H:%M:%S'), '%Y-%m-%d')
        start_time_today = local_date_now + ' 00:00:00'
        start_time_today_utc = self.env[
            'change.datetime'].change_local_datetime_to_utc(start_time_today,
                                                            '%Y-%m-%d %H:%M:%S')

        in_location_where_clause = \
                " and d.location_usage != 'internal' and d.location_dest_usage = 'internal'"

        out_location_where_clause = \
                " and d.location_usage = 'internal' and d.location_dest_usage != 'internal'"


        query_in = """
                    with d as(
                        select sm.id as id, 
                                sm.product_id as product_id,
                                sm.price_unit as price_unit,
                                sm.state as state,
                                sm.date_expected as date_expected,
                                sm.company_id as company_id,
                                sm.product_uom_qty as product_uom_qty,
                                sl.usage as location_usage, 
                                sl_1.usage as location_dest_usage
                        from stock_move as sm
                        left join stock_location as sl
                            on sm.location_id = sl.id
                        left join stock_location as sl_1
                            on sm.location_dest_id = sl_1.id
                        )
                    select sum(d.product_uom_qty * d.price_unit)
                        from d
                    where state = 'done' and date_expected >= '{}' {} and company_id = %s
                    
                """.format(start_time_today_utc, in_location_where_clause)
        cr.execute(query_in, [self.env.user.company_id.id])
        query_in_result = cr.fetchone()
        goods_receipt = query_in_result and query_in_result[0] or 0
        goods_receipt = self.format_money(goods_receipt)

        query_out = """
                            with d as(
                                select sm.id as id, 
                                        sm.product_id as product_id,
                                        sm.price_unit as price_unit,
                                        sm.state as state,
                                        sm.date_expected as date_expected,
                                        sm.company_id as company_id,
                                        sm.product_uom_qty as product_uom_qty,
                                        sl.usage as location_usage, 
                                        sl_1.usage as location_dest_usage
                                from stock_move as sm
                                left join stock_location as sl
                                    on sm.location_id = sl.id
                                left join stock_location as sl_1
                                    on sm.location_dest_id = sl_1.id
                                )
                            select sum(d.product_uom_qty * d.price_unit)
                                from d
                            where state = 'done' and date_expected >= '{}' {} and company_id = %s

                        """.format(start_time_today_utc, out_location_where_clause)
        cr.execute(query_out, [self.env.user.company_id.id])
        query_out_result = cr.fetchone()
        goods_issue = query_out_result and query_out_result[0] or 0
        goods_issue = self.format_money(goods_issue)
        querry = """
                    select sum(a.qty*a.cost)
                      from stock_quant a
                    where a.company_id = %s
                """
        cr.execute(querry, [self.env.user.company_id.id])
        querry_result = cr.fetchone()
        inventory = querry_result and querry_result[0] or 0
        inventory = self.format_money(inventory)

        querry = """
                    select count(*)
                    from account_invoice
                    where state != 'cancel'
                      and company_id = %s
                """
        cr.execute(querry, [self.env.user.company_id.id])
        querry_result = cr.fetchone()
        num_invoice = querry_result and querry_result[0] or 0

        return employee, inventory, num_invoice, goods_receipt, goods_issue

    def get_revenue_customer(self, from_date, to_date):
        query = """
                    select rp.id,
                        rp.name,
                        o.amount_untaxed_repair,
                        array_to_string(array_agg(c.name),', ') as categ
                    from sale_order as o
                        left join res_partner as rp
                        on rp.id = o.partner_id
                        left join res_partner_res_partner_category_rel as rel
                        on rp.id=rel.partner_id
                        left join res_partner_category as c
                        on c.id=rel.category_id
                    where o.create_date::date >= %s
                      and o.create_date::date <= %s
                      and o.state not in ('draft', 'cancel')
                      and o.company_id = %s
                    group by rp.id, rp.name, o.amount_untaxed_repair
                    order by o.amount_untaxed_repair desc
                    limit 5
                """

        self.env.cr.execute(
            query, [from_date, to_date,
                    self.env.user.company_id.id])
        data = [{
            'id': row['id'],
            'name': row['name'],
            'revenue': row['amount_untaxed_repair'] or 0,
            'categ': row['categ'],
                } for row in self.env.cr.dictfetchall()]
        return data

    def top_current_day_customer(
            self, **kw):

        from_date = to_date = datetime.datetime.now().strftime('%Y-%m-%d')

        data = self.get_revenue_customer(from_date, to_date)
        return data

    def top_revenue_customer(
            self, period='week', **kw):

        from_date, to_date, current = self.get_from_date_to_date(period)
        data = self.get_revenue_customer(from_date, to_date)
        return data

    def get_return_customer_rate_data(self):
        def subtract_month(month, year):
            if month == 1:
                return 12, year - 1
            return month - 1, year

        current_date = datetime.datetime.now()
        current_month = current_date.month
        current_year = current_date.year

        temp_labels = []
        index = 0
        for i in range(0,5):
            current_month, current_year = \
                subtract_month(current_month,
                               current_year)
            index += 1
            if index < 3:
                continue

            temp_labels.append('{}/{}'.format(
                current_month, current_year))

        labels = []
        for i in range(len(temp_labels), 0, -1):
            labels.append(temp_labels[i-1])

        customer_count = self.env['res.partner'
        ].search([('customer', '=', True)], count=True)


        query = """
                    with d1 as(
                    select o.partner_id as id, count(o.id) as count
                    from sale_order as o
                    where o.state in ('sale', 'done')
                      and o.confirmation_date < %s
                      and o.company_id = %s
                    group by o.partner_id),
                    d2 as(
                    select o.partner_id as id, count(o.id) as count
                    from sale_order as o
                    where o.state in ('sale', 'done')
                      and o.confirmation_date >= %s
                      and o.company_id = %s
                    group by o.partner_id)

                    select p.id, d1.count, d2.count
                    from res_partner as p
                    left join d1 on d1.id = p.id
                    left join d2 on d2.id = p.id
                    where d1.count >0 or d2.count > 0
                    and p.customer is true
                """

        type1_dict = {}
        type2_dict = {}

        for label in labels:
            month,year = label.split('/')
            condition_date = '{}-{}-01'.format(year, month)
            self.env.cr.execute(
                query,
                [condition_date, self.env.user.company_id.id,
                 condition_date, self.env.user.company_id.id])

            type1 = 0
            type2 = 0

            for row in self.env.cr.fetchall():
                partner_id = row[0]
                before_count = row[1]
                after_count = row[2]

                if before_count and not after_count:
                    type1 += 1

                if before_count and after_count:
                    type2 += 1

            type1_dict[label] = type1
            type2_dict[label] = type2

        data1 = [type1_dict.get(label, 0) for label in labels]
        percent1 = \
            [customer_count and round(type1_dict.get(label, 0)*100.0/customer_count,2) for label in labels]
        data2 = [type2_dict.get(label, 0) for label in labels]
        percent2 = \
            [customer_count and round(
                type2_dict.get(label, 0) * 100.0 / customer_count, 2) for label
             in labels]

        data = {
            'labels': labels,
            'datasets': [
                        {
                            'label': u"Số khách không tới trong 3 tháng gần nhất",
                            'backgroundColor': "#70db70",
                            'data': data1,
                            'percent': percent1,
                        },
                        {
                            'label': u"Khách hàng tới 1 lần và quay lại trong 3 tháng gần nhất",
                            'backgroundColor': "#6666ff",
                            'data': data2,
                            'percent': percent2
                        },
                    ]
                }
        return data

    def get_customer_number_times_data(self, **kw):
        query = """
                    with d as (
                        select o.partner_id as id, count(o.id) as times
                        from sale_order as o
                        where o.state in ('done', 'cancel')
                          and o.company_id = %s
                        group by o.partner_id
                        )
                    select times, count(id) as count
                    from d
                    group by times
                    order by count(id) desc
                    limit 10
                """
        self.env.cr.execute(query, [self.env.user.company_id.id])

        times_dict = {
            '1': 0,
            '2->5': 0,
            '>5': 0
        }

        total = 0
        for row in self.env.cr.dictfetchall():
            times = row['times']
            count = row['count']
            total += times * count

            if times == 1:
                times_dict['1'] = count
                continue

            if times >=2 and times <= 5:
                times_dict['2->5'] += count
                continue

            times_dict['>5'] += count

        labels = []
        colors = []
        data = []
        index = 0
        for key in times_dict.keys():
            color = self.get_color(index)

            labels.append(u'{} lượt'.format(key))
            data.append(times_dict[key])
            colors.append(color)
            index += 1

        total = u'{} lượt'.format(total)

        datas = {
            'labels': labels,
            'datasets': [
                {
                    'label': "Times number",
                    'data': data,
                    'backgroundColor': colors,
                    'borderColor': colors,
                    'borderWidth': [1 for d in data]
                }
            ],
            'inside_text': total,
        }
        return datas

    def get_top10_service_rate_data(self, period, **kw):
        revenue_account_type_id = \
            self.env.ref('account.data_account_type_revenue').id

        from_date, to_date, current = \
            self.get_from_date_to_date(period)

        query = """
                    with d as (
                    select pt.id,
                        pt.name,
                        sum(ml.credit - ml.debit) as balance
                    from product_template as pt
                        left join product_product as pp
                        on pp.product_tmpl_id = pt.id
                        left join account_move_line as ml
                        on ml.product_id = pp.id
                        left join account_account as aa
                        on aa.id = ml.account_id
                        left join account_move as am
                        on am.id = ml.move_id
                    where (pt.is_service_package is false
                        or pt.is_service_package is null)
                        and pt.type = 'service'
                        and aa.user_type_id = {account_type_id}
                        and am.state = 'posted'
                        and am.date >= '{from_date}'
                        and am.date <= '{to_date}'
                        and am.company_id = {company_id}
                    group by pt.id,
                        pt.name
                    )
                    select id, name, balance
                    from d
                    order by balance desc
                """.format(account_type_id=revenue_account_type_id,
                           from_date=from_date,
                           to_date=to_date,
                           company_id=self.env.user.company_id.id)
        self.env.cr.execute(query)

        labels = []
        colors = []
        data = []
        index = 0
        total = 0
        other = 0
        for row in self.env.cr.dictfetchall():
            name = row['name']
            balance = row['balance']
            total += balance
            index += 1

            if index > 10:
                other += balance
                continue

            labels.append(name)
            data.append(balance)
            color = self.get_color(index)
            colors.append(color)

        total = self.format_money(total, u'triệu')

        if other:
            color = self.get_color(11)
            labels.append(_('Other'))
            data.append(other)
            colors.append(color)

        datas = {
            'labels': labels,
            'datasets': [
                {
                    'label': "Product Service",
                    'data': data,
                    'backgroundColor': colors,
                    'borderColor': colors,
                    'borderWidth': [1 for d in data]
                }
            ],
            'inside_text': total,
        }
        return datas

    def get_top10_product_rate_data(self, period, **kw):
        revenue_account_type_id = \
            self.env.ref('account.data_account_type_revenue').id

        from_date, to_date, current = \
            self.get_from_date_to_date(period)

        query = """
                    with d as (
                    select pt.id,
                        pt.name,
                        sum(ml.credit - ml.debit) as balance
                    from product_template as pt
                        left join product_product as pp
                        on pp.product_tmpl_id = pt.id
                        left join account_move_line as ml
                        on ml.product_id = pp.id
                        left join account_account as aa
                        on aa.id = ml.account_id
                        left join account_move as am
                        on am.id = ml.move_id
                    where (pt.is_service_package is false
                        or pt.is_service_package is null)
                        and pt.type in ('product', 'consu')
                        and aa.user_type_id = {account_type_id}
                        and am.state = 'posted'
                        and am.date >= '{from_date}'
                        and am.date <= '{to_date}'
                        and am.company_id = {company_id}
                    group by pt.id,
                        pt.name
                    )
                    select id, name, balance
                    from d
                    order by balance desc
                """.format(account_type_id=revenue_account_type_id,
                           from_date=from_date,
                           to_date=to_date,
                           company_id=self.env.user.company_id.id)
        self.env.cr.execute(query)

        labels = []
        colors = []
        data = []
        index = 0
        total = 0
        other = 0
        for row in self.env.cr.dictfetchall():
            name = row['name']
            balance = row['balance']
            total += balance
            index += 1

            if index > 10:
                other += balance
                continue

            labels.append(name)
            data.append(balance)
            color = self.get_color(index)
            colors.append(color)

        total = self.format_money(total, u'triệu')

        if other:
            color = self.get_color(11)
            labels.append(_('Other'))
            data.append(other)
            colors.append(color)

        datas = {
            'labels': labels,
            'datasets': [
                {
                    'label': "Product Service",
                    'data': data,
                    'backgroundColor': colors,
                    'borderColor': colors,
                    'borderWidth': [1 for d in data]
                }
            ],
            'inside_text': total,
        }
        return datas

    def get_qty_inventory_by_warehouse_rate_data(self, **kw):
        query = """
                    select l.id,
                    sum(q.qty)
                    from stock_quant as q
                      left join stock_location as l
                      on q.location_id = l.id
                    where l.usage = 'internal'
                      and q.company_id = %s
                    group by l.id
                """
        self.env.cr.execute(query, [self.env.user.company_id.id])
        query_result = self.env.cr.fetchall()

        location_s = self.env['stock.location'].search([('usage','=','internal')])
        location_dict = \
            dict((location.id, location.name) for location in location_s)

        labels = []
        data = []
        colors = []

        index = 0

        for row in query_result:
            location_id = row[0]
            location_name = location_dict.get(
                location_id, u'Không xác định')
            labels.append(location_name)

            qty = row[1]
            data.append(qty)

            colors.append(self.get_color(index))
            index += 1

        datas = {
            'labels': labels,
            'datasets': [
                {
                    'label': "Inventory by warehouse",
                    'data': data,
                    'backgroundColor': colors,
                    'borderColor': colors,
                    'borderWidth': [1 for d in data]
                }
            ],
            'inside_text': '',
        }
        return datas

    def get_value_inventory_by_warehouse_rate_data(self, **kw):
        query = """
                    select l.id,
                      q.qty, q.cost,
                      q.product_id
                    from stock_quant as q
                      left join stock_location as l
                      on q.location_id = l.id
                    where l.usage = 'internal'
                      and q.company_id = %s
                """
        self.env.cr.execute(query, [self.env.user.company_id.id])
        query_result = self.env.cr.fetchall()

        location_s = self.env['stock.location'].search(
            [('usage', '=', 'internal')])
        location_dict = \
            dict((location.id, location.name) for location in location_s)

        labels = []
        data = []
        colors = []

        product_ids = [row[3] for row in query_result]
        product_s = self.env['product.product'].browse(product_ids)
        standard_price_dict = \
            dict((product.id, product.standard_price) for product in product_s)

        location_value_dict = {}
        labels_dict = {}

        index = 0
        for row in query_result:
            location_id = row[0]
            qty = row[1]
            cost = row[2]
            product_id = row[3]
            location_name = location_dict.get(
                location_id, u'Không xác định')

            labels_dict[location_id] = location_name

            if not cost:
                cost = standard_price_dict.get(product_id, 0)

            value = qty * cost

            if not location_value_dict.get(location_id, False):
                location_value_dict[location_id] = 0

            location_value_dict[location_id] += value

            colors.append(self.get_color(index))
            index += 1

        for location_id in location_value_dict.keys():
            labels.append(labels_dict.get(location_id, u'Không xác định'))
            data.append(location_value_dict.get(location_id, 0))

        datas = {
            'labels': labels,
            'datasets': [
                {
                    'label': "Inventory by warehouse",
                    'data': data,
                    'backgroundColor': colors,
                    'borderColor': colors,
                    'borderWidth': [1 for d in data]
                }
            ],
            'inside_text': '',
        }
        return datas

    def get_top_inventory_qty_data(self, stock_id, **kw):
        labels = []
        data = []
        colors = []

        query = """
                    select q.product_id, pt.name,
                    sum(q.qty)
                     from stock_quant as q
                     left join product_product as pp
                      on pp.id = q.product_id
                     left join product_template as pt
                      on pt.id = pp.product_tmpl_id
                    where q.location_id = %s
                      and q.company_id = %s
                    group by q.product_id, pt.name
                    limit 10
                """

        self.env.cr.execute(
            query, [stock_id, self.env.user.company_id.id])

        total = 0
        index = 0
        for row in self.env.cr.fetchall():
            product_id = row[0]
            product_name = row[1]
            inventory = row[2]

            data.append(inventory)
            labels.append(product_name)
            total += inventory
            colors.append(self.get_color(index))

            index += 1

        datas = {
            'labels': labels,
            'datasets': [
                {
                    'label': "Inventory by warehouse",
                    'data': data,
                    'backgroundColor': colors,
                    'borderColor': colors,
                    'borderWidth': [1 for d in data]
                }
            ],
            'inside_text': u'{} Sản phẩm'.format(total),
        }
        return datas

    def get_top_inventory_value_data(self, stock_id, **kw):
        query = """
                    select q.product_id,
                      q.qty,
                      q.cost
                    from stock_quant as q
                    where q.location_id = %s
                      and q.company_id = %s
                    limit 10
                """
        self.env.cr.execute(
            query, [stock_id, self.env.user.company_id.id])
        query_result = self.env.cr.fetchall()

        labels = []
        data = []
        colors = []

        product_ids = [row[0] for row in query_result]
        product_s = self.env['product.product'].browse(product_ids)
        product_dict = \
            dict((product.id, product) for product in product_s)

        product_value_dict = {}
        labels_dict = {}
        for row in query_result:
            product_id = row[0]
            qty = row[1]
            cost = row[2]

            product = product_dict.get(product_id, False)

            if not product:
                continue

            labels_dict[product.id] = product.name

            if not cost:
                cost = product.standard_price

            value = qty * cost

            if not product_value_dict.get(product.id, False):
                product_value_dict[product.id] = 0

            product_value_dict[product.id] += value

        index = 0
        total = 0
        for product_id in product_value_dict.keys():
            labels.append(labels_dict.get(product_id, u'Không xác định'))
            value = product_value_dict.get(product_id, 0)
            data.append(value)
            total += value

            colors.append(self.get_color(index))
            index += 1

        total = self.format_money(total, u'triệu')

        datas = {
            'labels': labels,
            'datasets': [
                {
                    'label': "Inventory by product",
                    'data': data,
                    'backgroundColor': colors,
                    'borderColor': colors,
                    'borderWidth': [1 for d in data]
                }
            ],
            'inside_text': total,
        }
        return datas

    def get_top_purchase_qty_chart_data(self, period, **kw):
        labels = []
        data = []
        colors = []

        from_date, to_date, current = \
            self.get_from_date_to_date(period)

        query = """
                  select il.product_id,
                    pt.name,
                    sum(il.quantity) as qty
                  from account_invoice_line as il
                    left join account_invoice as i
                        on i.id = il.invoice_id
                    left join product_product as pp
                        on pp.id = il.product_id
                    left join product_template as pt
                        on pt.id = pp.product_tmpl_id
                  where i.type = 'in_invoice'
                      and i.state not in ('draft', 'cancel')
                      and i.date_invoice >= %s
                      and i.date_invoice <= %s
                      and i.company_id = %s
                  group by il.product_id, pt.name
                  limit 10
                """

        self.env.cr.execute(
            query, [from_date, to_date,
                    self.env.user.company_id.id])


        index = 0
        for row in self.env.cr.fetchall():
            product_id = row[0]
            product_name = row[1]
            qty = row[2]

            data.append(qty)
            labels.append(product_name)
            colors.append(self.get_color(index))

            index += 1

        datas = {
            'labels': labels,
            'datasets': [
                {
                    'label': "Inventory by warehouse",
                    'data': data,
                    'backgroundColor': colors,
                    'borderColor': colors,
                    'borderWidth': [1 for d in data]
                }
            ],
            'inside_text': u'',
        }
        return datas

    def get_top_purchase_value_item_data(self, period, **kw):
        from_date, to_date, current = \
            self.get_from_date_to_date(period)

        query = """
                  select il.product_id,
                    pt.name,
                    sum(il.quantity) as qty,
                    sum(il.price_subtotal) as price_subtotal
                  from account_invoice_line as il
                    left join account_invoice as i
                        on i.id = il.invoice_id
                    left join product_product as pp
                        on pp.id = il.product_id
                    left join product_template as pt
                        on pt.id = pp.product_tmpl_id
                  where i.type = 'in_invoice'
                      and i.state not in ('draft', 'cancel')
                      and i.date_invoice >= %s
                      and i.date_invoice <= %s
                      and i.company_id = %s
                  group by il.product_id, pt.name
                  limit 10
                """

        self.env.cr.execute(query, [from_date, to_date,
                                    self.env.user.company_id.id])

        datas = []
        for row in self.env.cr.fetchall():
            product_id = row[0]
            product_name = row[1] or _('Undefine')
            qty = row[2]
            price_subtotal = row[3]

            datas.append({
                'name': product_name,
                'qty': qty,
                'value': price_subtotal
            })
        sorted_datas = sorted(datas, key=itemgetter('value'), reverse=True)

        return sorted_datas

    def get_top_supplier(self, period, order):
        query = """
                with d as(
		          select i.partner_id,
                    rp.name,
                    sum(il.quantity) as qty,
                    sum(il.price_subtotal) as price_subtotal
                  from account_invoice_line as il
                    left join account_invoice as i
                        on i.id = il.invoice_id
                    left join res_partner as rp
                        on rp.id = i.partner_id
                  where i.type = 'in_invoice'
                      and i.state not in ('draft', 'cancel')
                      and i.date_invoice >= %s
                      and i.date_invoice <= %s
                      and i.company_id = %s
                  group by i.partner_id,
                    rp.name
                    )
                   select partner_id, name, qty, price_subtotal
                   from d
                   order by {} desc
                   limit 10
                """.format(order)
        from_date, to_date, current = \
            self.get_from_date_to_date(period)
        self.env.cr.execute(query,
                            [from_date, to_date,
                             self.env.user.company_id.id])
        return self.env.cr.fetchall()

    def get_top_supplier_qty_chart_data(self, period, **kw):
        labels = []
        data = []
        colors = []

        total = 0
        index = 0
        for row in self.get_top_supplier(period, 'qty'):
            partner_id = row[0]
            partner_name = row[1]
            qty = row[2]
            price_subtotal = row[3]

            data.append(qty)
            labels.append(partner_name)
            colors.append(self.get_color(index))

            total += qty

            index += 1

        datas = {
            'labels': labels,
            'datasets': [
                {
                    'label': "Top qty purchase by supplier",
                    'data': data,
                    'backgroundColor': colors,
                    'borderColor': colors,
                    'borderWidth': [1 for d in data]
                }
            ],
            'inside_text': u'{} Sản phẩm'.format(total),
        }
        return datas

    def get_top_supplier_value_chart_data(self, period, **kw):
        labels = []
        data = []
        colors = []

        total = 0
        index = 0
        for row in self.get_top_supplier(period, 'price_subtotal'):
            partner_id = row[0]
            partner_name = row[1]
            qty = row[2]
            price_subtotal = row[3]

            data.append(price_subtotal)
            labels.append(partner_name)
            colors.append(self.get_color(index))

            total += price_subtotal

            index += 1

        total = self.format_money(total, u' triệu')

        datas = {
            'labels': labels,
            'datasets': [
                {
                    'label': "Top value purchase by supplier",
                    'data': data,
                    'backgroundColor': colors,
                    'borderColor': colors,
                    'borderWidth': [1 for d in data]
                }
            ],
            'inside_text': total,
        }
        return datas

    def get_top_sale_again_data(self, period):
        from_date, to_date, current = self.get_from_date_to_date(period)

        query = """
                    with d as (
                        select pol.product_id as id,
                            pt.name,
                            count(*) as pol_number
                        from purchase_order_line as pol
                            left join purchase_order as po
                            on po.id = pol.order_id
                            left join product_product as pp
                            on pp.id = pol.product_id
                            left join product_template as pt
                            on pt.id = pp.product_tmpl_id
                        where po.date_order::date >= %s
                            and po.date_order::date <= %s
                            and po.state in ('purchase', 'done')
                            and po.company_id = %s
                        group by pol.product_id, pt.name
                        )
                    select d.id, d.name, d.pol_number
                    from d
                    order by pol_number desc
                    limit 10
                """

        self.env.cr.execute(query,
                            [from_date, to_date,
                             self.env.user.company_id.id])
        datas = [{
                     'name': row[1],
                     'qty': row[2]
                 } for row in self.env.cr.fetchall()]

        return datas

    def get_top_delivery_data(self, period, **kw):
        from_date, to_date, current = \
            self.get_from_date_to_date(period)

        query = """
                    with d as (
                        select
                        pt.id as pt_id,
                        pt.name as name,
                        min(extract(epoch from sm.date - sm.create_date)) as delay
                                from stock_move as sm
                                    left join stock_picking as sp
                                    on sp.id = sm.picking_id
                                    left join product_product as pp
                                    on pp.id = sm.product_id
                                    left join product_template pt
                                    on pt.id = pp.product_tmpl_id
                                where sm.purchase_line_id is not null
                                    and sm.state = 'done'
                                    and sm.create_date::date >= %s
                                    and sm.create_date::date <= %s
                                    and sm.company_id = %s
                                group by pt.id, pt.name
                         )
                         select pt_id, name, delay
                         from d
                         order by delay
                         limit 10
                """
        self.env.cr.execute(
            query,
            [from_date, to_date,
             self.env.user.company_id.id])

        result = self.env.cr.fetchall()

        datas = []

        for row in result:
            name = row[1]
            delay = row[2]

            delay = str(round(delay/86400, 2)) + u' Ngày'

            datas.append({
                'name': name,
                'for': delay
            })
        return datas

    def get_customer_pie_chart_datas(self):
        customer_number = self.get_customer_number()
        total = customer_number['total']
        data = {u"Khách": []}
        for categ in customer_number['types']:
            name = categ[0]
            number = categ[1]
            data[u"Khách"].append(
                {
                    "sector": name,
                    "size": number
                }
            )
        return data, total

    def m_main_report(self, type):
        datas = self.get_main_report_datas(type)
        return datas
