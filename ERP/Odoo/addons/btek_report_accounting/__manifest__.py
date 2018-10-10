# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'B Tek Report Accounting',
    'version' : '1.0',
    'summary': 'B Tek Report Accounting',
    'sequence': 1,
    'description': """
        B Tek Report Accounting """,
    'category': 'Accounting',
    'depends' : ['account', 'report_xlsx'],
    'data': [
                'views/BC_so_cttk_view.xml',
                'views/sochitietcongno.xml',
                'views/BC_bang_cdps_view.xml',
                'views/so_quy.xml',
                'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
