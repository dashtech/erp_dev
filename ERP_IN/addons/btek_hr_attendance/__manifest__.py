# -*- coding: utf-8 -*-
{
    'name': 'BTek Hr Attendance',
    'version': '10.0.1.2.3',
    'author': 'Bave technology',
    'summary': 'BTek Hr',
    'sequence': 17,
    'category': 'HRM',
    'website': 'http://bave.io/',
    'images': [],
    'depends': [
        'hr_attendance',
        'report_xlsx',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_import_attendance_view.xml',
        # 'views/hr_worked_day_view.xml',
        'views/report_view.xml',
        'views/import_failed_form.xml'
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
