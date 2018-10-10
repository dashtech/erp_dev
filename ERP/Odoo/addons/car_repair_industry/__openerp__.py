# -*- coding: utf-8 -*-
##############################################################################
#
#    This module uses OpenERP, Open Source Management Solution Framework.
#    Copyright (C) 2015-Today BrowseInfo (<http://www.browseinfo.in>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

{
    "name" : "Car Repair/Maintenance Management",
    "version" : "1.0",
    "depends" : ['sale_stock', 'mail', 'account',
                 'product', 'stock', 'survey', 'fleet',
                 'pos_coupons', 'pos_loyalty_management',
                 'mrp', 'btek_account_payment', 'btek_account',
                 'btek_report_stock', 'btek_sale', 'wk_coupons',
                 'account_cancel', 'inputmask_widget', 'toolz',],
    "author": "BrowseInfo",
    'sequence': 1,
    "summary": "Car Maintenance Repair management module helps to manage repair order, repair diagnosis, Diagnosis report,Workorder,Quote/Sales/Invoicing Whole workflow of Repair Industry",
    "description": """
    BrowseInfo developed a new odoo/OpenERP module apps.
    This module use for autorepair industry , workshop management, Car Repair service industry, Spare parts industry. Fleet repair management. Vehicle Repair shop, Mechanic workshop, Mechanic repair software.Maintenance and Repair car. Car Maintenance Spare Part Supply. Car Servicing, Auto Servicing, Auto mobile Service, Bike Repair Service. Maintenance and Operation.Car Maintenance Repair management module helps to manage repair order, repair diagnosis, Diagnosis report, Diagnosis analysis, Quote for Repair, Invoice for Repair, Repair invoice, Repair orders, Workorder for repair, Fleet Maintenance.

    """,
    'category': 'Extra Tools',
    'price': '380.00',
    'currency': "EUR",
    "website" : "www.browseinfo.in",
    "data" :[
        'security/fleet_repair_security.xml',
        'security/ir.model.access.csv',

        'wizard/repair_coupon_view.xml',
        'wizard/fleet_repair_reason_view.xml',

        'data/custom_sale_sequance.xml',
        'data/decimal_precision.xml',
        'report/customize_herder_footer_report.xml',
        'report/fleet_repair_label_view.xml',
        'report/fleet_repair_label_menu.xml',
        'report/fleet_repair_receipt_view.xml',
        'report/fleet_repair_receipt_menu.xml',
        'report/fleet_diagnostic_result_report_view.xml',
        'report/fleet_diagnostic_result_report_menu.xml',
        'report/fleet_workorder_report_view.xml',
        'report/fleet_workorder_report_menu.xml',

        'report/report_invoice.xml',
        'report/report_stock_picking.xml',
        'report/receipts_from_account_invoice_view.xml',
        'report/repair_order_report.xml',
        'report/repair_order_report_menu.xml',
        'report/accessories_report.xml',
        'report/sale_order_report.xml',

        'views/fleet_repair_view.xml',
        'views/fleet_repair_sequence.xml',
        'views/fleet_diagnose_view.xml',
        'views/survey.xml',

        'views/voucher.xml',
        'views/fleet_workorder_sequence.xml',
        'views/fleet_workorder_view.xml',
        'views/sale_order_inherit_search.xml',
        'views/custom_sale_view.xml',
        'views/fleet_fleet_view.xml',
        'views/customer_inherit_seach_view.xml',

        #duongnh
        'views/fleet_repair_templates.xml',

        'views/be_dynamic_mapping_view.xml',
        'views/notification_view.xml',
        'views/purchase_view.xml',
        #
        'views/stock_picking_view.xml',

        'views/so_css.xml',
        'views/repair_config.xml',
    ],
    'qweb':[
        'static/src/xml/base.xml',
    ],
    "css": [
        'static/src/css/sale_order.css',
    ],
    "auto_install": False,
    "installable": True,
    "images":['static/description/Banner.png'],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
