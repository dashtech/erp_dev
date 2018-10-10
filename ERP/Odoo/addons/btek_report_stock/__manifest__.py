# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'BTek Report Stock',
    'version' : '1.0',
    'summary': 'BTek Report Stock',
    'sequence': 1,
    'description': """
        B Tek Report Stock""",
    'category': 'Stock',
    'depends': ['stock', 'report_xlsx', 'account', 'btek_localization', 'btek_stock_move_aml_rel'],
    'data': [
                'views/stock_inout.xml',
                'views/stock_inventory_account.xml',
                'views/stock_inventory_nxt.xml',
                'report/delivery_oder_report.xml',
                'report/receiving_oder_report.xml',
                'report/report_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
