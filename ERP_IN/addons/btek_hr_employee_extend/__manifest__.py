# -*- coding: utf-8 -*-
{
    'name': 'BTek Hr Extend',
    'version': '10.0.1.2.3',
    'author': 'Bave technology',
    'summary': 'BTek Hr',
    'sequence': 15,
    'category': 'HRM',
    'website': 'http://bave.io/',
    'images': [],
    'depends': [
        'hr',
        'hr_payroll',
        'hr_timesheet_sheet',
        'inputmask_widget',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/employee_rule.xml',

        'views/related_person_view.xml',
        'views/hr_employee_extend_view.xml',
        'views/hr_contract_inherit.xml',
        'views/hr_contract_config.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
