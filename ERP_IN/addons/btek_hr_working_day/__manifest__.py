# -*- coding: utf-8 -*-
{
    'name': 'BTek Hr Working Day',
    'version': '10.0.1.2.3',
    'author': 'Bave technology',
    'summary': 'BTek Hr',
    'sequence': 17,
    'category': 'HRM',
    'website': 'http://bave.io/',
    'images': [],
    'depends': [
        'hr_timesheet',
        'btek_hr_holiday'
        # 'report_xlsx',
    ],
    'data': [
        'views/btek_hr_working_day_templates.xml',
        'views/hr_working_day_view.xml',
        'views/hr_import_working_day.view.xml',
        'views/import_failed_form.xml',
        'views/report_view.xml',
        'security/ir.model.access.csv',
        'views/hr_working_day_employee.xml',
    ],
    'demo': [
    ],
    'qweb': ['static/src/xml/btek_timesheet.xml', ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
