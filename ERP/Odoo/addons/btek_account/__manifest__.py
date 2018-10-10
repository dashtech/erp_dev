# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Accounting',
    'version': '1.0',
    'category': 'Invoice',
    'summary': 'Accounting',
    'description': """
    Customize accounting Viet Nam
""",
    'website': 'https://www.odoo.com',
    'depends': ['account', 'analytic', 'account_asset', 'toolz'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_invoice.xml',
        'views/menu.xml',
        'views/company.xml',
        'views/import_account_account.xml',
        'views/import_customer_receivable.xml',
        'views/import_supplier_receivable.xml',
        'views/import_account_balance.xml',
        'views/account_tax.xml',
        # 'security/ir.model.access.csv',
        'views/account_invoice_inherit.xml',
        'views/account_payment_inherit.xml',
        'report/report_invoice.xml',
    ],
    'qweb': [
        'static/src/xml/account_payment.xml',
    ],
    'demo': [

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
