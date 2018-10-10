# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo import tools
from datetime import datetime, timedelta


class WizardReportRevenue(models.TransientModel):
    _name = 'wizard.report.revenue'
    _description = 'wizard.report.revenue'

    def get_default_from_date(self):
        current_year = datetime.now().year
        fisrt_day_of_current_year = \
            '{}-01-01'.format(current_year)
        return fisrt_day_of_current_year

    def get_default_to_date(self):
        current_day = datetime.now().strftime('%Y-%m-%d')
        return current_day

    from_date = fields.Date(required=True,
                            default=get_default_from_date)
    to_date = fields.Date(required=True,
                          default=get_default_to_date)
    product_categ_ids = fields.Many2many(
        'product.category',
        'wizard_report_revenue_product_categ_rel',
        'wizard_id', 'categ_id',
        string='Product categories'
    )
    company_id = fields.Many2one(
        'res.company', 'Company', required=True,
        default=lambda s:s.env.user.company_id.id)

    _sql_constraints = [
        ('check_from_date_to_date_uniq',
         'CHECK(from_date<=to_date)',
         _('From date must be less than or equal to date !')),
    ]

    def export_report(self):
        datas = {'ids': self.ids}
        datas['model'] = 'wizard.report.revenue'
        datas['data'] = self.read()[0]
        for field in datas['data'].keys():
            if isinstance(datas['data'][field], tuple):
                datas['data'][field] = datas['data'][field][0]

        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'btek_account_report.report.revenue.xlsx',
            'datas': datas,
            'name': _('Report revenue')
        }

    def get_month_list(self, from_date, to_date):
        def get_month_year(date_obj):
            return '{}/{}'.format(
                date_obj.month,
                date_obj.year
            )
        from_date_obj = datetime.strptime(
            from_date, '%Y-%m-%d')

        to_date_obj = datetime.strptime(
            to_date, '%Y-%m-%d')

        month_list = [get_month_year(from_date_obj)]

        while from_date_obj < to_date_obj:
            month_year = get_month_year(from_date_obj)
            if month_year not in month_list:
                month_list.append(month_year)

            next_month = from_date_obj.month + 1
            next_year = from_date_obj.year
            if next_month == 13:
                next_month = 1
                next_year += 1

            from_date_obj = datetime.strptime(
                '{}-{}-01'.format(next_year, next_month),
                '%Y-%m-%d'
            )
        return month_list

    @api.multi
    def get_data(self):
        from_date = self[0].from_date
        to_date = self[0].to_date
        company_id = self[0].company_id.id

        month_list = self.get_month_list(from_date, to_date)

        product_categ_ids = \
            self[0].product_categ_ids._ids
        product_categ_condition = ''

        if product_categ_ids:
            product_categ_condition = \
                ' and pt.categ_id in (' + \
                ','.join([str(categ_id) for categ_id in product_categ_ids]) + ')'

        revenue_account_type_id = \
            self.env.ref('account.data_account_type_revenue').id

        querry = """
                    select
                        extract(month from am.date::date) as month,
                        extract(year from am.date::date) as year,
                        ml.product_id as product_id,
                        pt.name as product_name,
                        pt.list_price as list_price,
                        sum(ml.quantity) as qty,
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
                      and am.date >= %s
                      and am.date <= %s
                      and ml.company_id = {company_id}
                      {product_categ_condition}
                    group by
                      ml.product_id,
                      pt.name,
                      pt.list_price,
                      extract(month from am.date::date),
                      extract(year from am.date::date)
                """.format(
            revenue_account_type_id=revenue_account_type_id,
            company_id=company_id,
            product_categ_condition=product_categ_condition)

        self.env.cr.execute(querry,
                            [from_date, to_date])
        product_dict = {}
        total_dict = {}
        for row in self.env.cr.dictfetchall():
            month = row['month']
            year = row['year']
            month_year = '{}/{}'.format(int(month), int(year))
            product_id = row['product_id'] or 0
            qty = row['qty'] or 0
            balance = row['balance'] or 0

            if not product_dict.get(product_id, False):
                product_dict[product_id] = {
                    'name': row['product_name'] or _('Undefine'),
                    'list_price': row['list_price'] or 0,
                    'progressive': 0,
                    'balance': {},
                }

            if not product_dict[product_id]['balance'
            ].get(month_year, False):
                product_dict[product_id]['balance'][month_year] = \
                    {
                        'qty': 0,
                        'balance': 0,
                    }
            product_dict[product_id]['balance'
            ][month_year]['qty'] += qty

            product_dict[product_id]['balance'
            ][month_year]['balance'] += balance

            product_dict[product_id]['progressive'] += balance

            if not total_dict.get(month_year, False):
                total_dict[month_year] = \
                    {
                        'qty': 0,
                        'balance': 0,
                    }

            total_dict[month_year]['qty'] += qty
            total_dict[month_year]['balance'] += balance

        total = sum(
            [total_dict.get(month_year, {}).get('balance', 0)
             for month_year in month_list]
        )

        return product_dict,month_list,total_dict,total,from_date,to_date
