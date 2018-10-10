# -*- coding: utf-8 -*-
{
    'name': 'BTek Hr Payroll data',
    'version': '10.0.1.2.3',
    'author': 'Bave technology',
    'summary': 'BTek Hr',
    'sequence': 5,
    'category': 'BTek Hr',
    'website': 'http://bave.io/',
    'images': [],
    'depends': [
        'hr',
        'hr_holidays',
        'hr_payroll',
        'btek_hr_employee_extend',
        'hr_payroll_account',
    ],
    'data': [
        'data/hr_payroll_rule_data.xml',

    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
