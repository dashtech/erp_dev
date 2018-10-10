# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Btek Pay',
    'version': '1.0',
    'category': 'Voucher',
    'summary': 'Accounting',
    'description': """
    Customize accounting Viet Nam/ Anhtt./
""",
    'website': 'https://www.odoo.com',
    'depends': ['account_voucher', 'btek_product', 'toolz'],
    'data': [
            'report_voucher/report_view.xml',
            'views/account_voucher.xml',
            'views/account_payment.xml',
            'report_voucher/account_voucher_report.xml',
            'report_voucher/account_payment_report.xml',
            'security/ir.model.access.csv',
    ],
    'demo': [

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
