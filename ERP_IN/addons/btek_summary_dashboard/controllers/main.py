# -*- coding: utf-8 -*-
import datetime
from odoo import http
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.tools.translate import _
import json
from operator import itemgetter

class MainReport(http.Controller):
    @http.route(
        ['/summary-report/',
         '/summary-report/<string:type>'],
        auth='user', website=True)
    def main_report(self, type='revenue', **kw):

        datas = http.request.env['summary.report.api'
        ].get_main_report_datas(type, **kw)

        return http.request.render(
            'btek_summary_dashboard.summary_report_template',
            datas)

    @http.route(['/set-user-company/<int:company_id>'],
                auth='user', website=True)
    def set_user_company(self, company_id):
        res = http.request.env['summary.report.api'
        ].set_user_company(company_id)
        return json.dumps(res)

    @http.route(['/get_revenue_area_chart_datas/',
                 '/get_revenue_area_chart_datas/<string:type>/<string:period>'],
                auth='user', website=True)
    def get_revenue_area_chart_datas(
            self, type='revenue', period='week',  **kw):
        data = http.request.env['summary.report.api'
        ].get_revenue_area_chart_datas(
            type=type, period=period, **kw)
        res = json.dumps(data)
        return res

    @http.route(['/get_customer_pie_chart_datas/'],
                auth='user', website=True)
    def get_customer_pie_chart_datas(
            self,  **kw):
        data = http.request.env['summary.report.api'
        ].get_customer_pie_chart_datas(**kw)

        res = json.dumps(data)
        return res

    @http.route(['/get_car_in_pie_chart_datas/'],
                auth='user', website=True)
    def get_car_in_pie_chart_datas(
            self, **kw):
        data = http.request.env['summary.report.api'
        ].get_car_in_pie_chart_datas(**kw)

        res = json.dumps(data)

        # print 'get_car_in_pie_chart_datas'
        # print data

        return res

    @http.route(['/get_car_in_area_chart_datas/',
                 '/get_car_in_area_chart_datas/<string:period>'],
                auth='user', website=True)
    def get_car_in_area_chart_datas(self, period='week', **kw):

        datas = http.request.env['summary.report.api'
        ].get_car_in_area_chart_datas(
            period=period, **kw)

        res = json.dumps(datas)
        return res

    @http.route(['/get_car_in_multi_line_chart_datas/',
                 '/get_car_in_multi_line_chart_datas/<string:period>'],
                auth='user', website=True)
    def get_car_in_multi_line_chart_datas(self, period='week', **kw):
        datas = http.request.env['summary.report.api'
        ].get_car_in_multi_line_chart_datas(
            period=period, **kw)

        res = json.dumps(datas)
        return res

    @http.route(['/top_revenue_customer_url/<string:period>'],
                auth='user', website=True)
    def get_top_revenue_customer(self, period='week', **kw):
        datas = http.request.env['summary.report.api'
        ].top_revenue_customer(
            period=period, **kw)
        res = json.dumps(datas)
        return res

    @http.route(['/get_customer_multi_line_chart_datas/',
                 '/get_customer_multi_line_chart_datas/<string:period>'],
                auth='user', website=True)
    def get_customer_multi_line_chart_datas(self, period='week', **kw):
        datas = http.request.env['summary.report.api'
        ].get_customer_multi_line_chart_datas(
            period=period, **kw)

        res = json.dumps(datas)
        return res

    @http.route(['/revenue-cost-product-type-pie-chart/<string:type>/<string:period>'],
                auth='user', website=True)
    def get_revenue_cost_product_type_pie_chart(self, type, period, **kw):
        data = http.request.env['summary.report.api'
        ].get_revenue_cost_product_type_pie_chart(type, period)

        res = json.dumps(data)
        return res

    @http.route(['/product-revenue-cost-period/<string:type>/<string:period>'],
                auth='user', website=True)
    def product_revenue_cost_period(self, type, period, **kw):

        data = http.request.env['summary.report.api'
        ].get_product_revenue_cost_period(type, period)

        res = json.dumps(data)
        return res

    @http.route(['/get_return_customer_rate/'],
                auth='user', website=True)
    def get_get_return_customer_rate_data(self, **kw):
        datas = http.request.env['summary.report.api'
        ].get_return_customer_rate_data(**kw)

        res = json.dumps(datas)
        return res

    @http.route(['/customer-number-times/'],
                auth='user', website=True)
    def get_customer_number_times_data(self, **kw):
        datas = http.request.env['summary.report.api'
        ].get_customer_number_times_data(**kw)

        res = json.dumps(datas)
        return res

    @http.route(['/product_service_rate/<string:period>'],
                auth='user', website=True)
    def get_product_service_rate_data(self, period, **kw):
        datas = http.request.env['summary.report.api'
        ].get_product_service_rate_data(period)

        res = json.dumps(datas)
        return res

    @http.route(['/top10_service_package_rate/<string:period>'],
                auth='user', website=True)
    def get_top10_service_package_rate_data(self, period, **kw):
        datas = http.request.env['summary.report.api'
        ].get_top10_service_package_rate_data(period, **kw)

        res = json.dumps(datas)
        return res

    @http.route(['/top10_service_rate/<string:period>'],
                auth='user', website=True)
    def get_top10_service_rate_data(self, period='week', **kw):
        datas = http.request.env['summary.report.api'
        ].get_top10_service_rate_data(period, **kw)

        res = json.dumps(datas)
        return res

    @http.route(['/top10_product_rate/<string:period>'],
                auth='user', website=True)
    def get_top10_product_rate_data(self, period='week', **kw):
        datas = http.request.env['summary.report.api'
        ].get_top10_product_rate_data(period, **kw)

        res = json.dumps(datas)
        return res

    @http.route(['/qty_inventory_by_warehouse_rate/'],
                auth='user', website=True)
    def get_qty_inventory_by_warehouse_rate_data(self, **kw):
        datas = http.request.env['summary.report.api'
        ].get_qty_inventory_by_warehouse_rate_data(**kw)

        res = json.dumps(datas)
        return res

    @http.route(['/value_inventory_by_warehouse_rate/'],
                auth='user', website=True)
    def get_value_inventory_by_warehouse_rate_data(self, **kw):
        datas = http.request.env['summary.report.api'
        ].get_value_inventory_by_warehouse_rate_data(**kw)

        res = json.dumps(datas)
        return res

    @http.route(['/top_inventory_value/<int:stock_id>/'],
                auth='user', website=True)
    def get_top_inventory_value_data(self, stock_id=0, **kw):
        datas = http.request.env['summary.report.api'
        ].get_top_inventory_value_data(stock_id, **kw)

        res = json.dumps(datas)
        return res

    @http.route(['/top_inventory_qty/<int:stock_id>/'],
                auth='user', website=True)
    def get_top_inventory_qty_data(self, stock_id=0, **kw):
        datas = http.request.env['summary.report.api'
        ].get_top_inventory_qty_data(stock_id, **kw)

        res = json.dumps(datas)
        return res

    @http.route(['/top_purchase_qty_chart/<string:period>/'],
                auth='user', website=True)
    def get_top_purchase_qty_chart_data(self, period='week', **kw):
        datas = http.request.env['summary.report.api'
        ].get_top_purchase_qty_chart_data(period, **kw)

        res = json.dumps(datas)
        return res

    @http.route(['/top_purchase_value_item/<string:period>/'],
                auth='user', website=True)
    def get_top_purchase_value_item_data(self, period='week', **kw):
        datas = http.request.env['summary.report.api'
        ].get_top_purchase_value_item_data(period, **kw)

        res = json.dumps(datas)
        return res

    @http.route(['/top_supplier_qty_chart/<string:period>/'],
                auth='user', website=True)
    def get_top_supplier_qty_chart_data(self, period='week', **kw):
        datas = http.request.env['summary.report.api'
        ].get_top_supplier_qty_chart_data(period, **kw)

        res = json.dumps(datas)
        return res

    @http.route(['/top_supplier_value_chart/<string:period>/'],
                auth='user', website=True)
    def get_top_supplier_value_chart_data(self, period='week', **kw):
        datas = http.request.env['summary.report.api'
        ].get_top_supplier_value_chart_data(period, **kw)

        res = json.dumps(datas)
        return res

    @http.route(['/top_sale_again/<string:period>/'],
                auth='user', website=True)
    def get_top_sale_again_data(self, period='week', **kw):
        datas = http.request.env['summary.report.api'
        ].get_top_sale_again_data(period, **kw)

        res = json.dumps(datas)
        return res

    @http.route(['/top_delivery/<string:period>/'],
                auth='user', website=True)
    def get_top_delivery_data(self, period='week', **kw):
        datas = http.request.env['summary.report.api'
        ].get_top_delivery_data(period, **kw)

        res = json.dumps(datas)
        return res
