# -*- coding: utf-8 -*-
{
    'name': 'BTek Hr Holidays',
    'version': '10.0.1.2.3',
    'author': 'Bave technology',
    'summary': 'BTek Hr',
    'sequence': 5,
    'category': 'BTek Module',
    'website': 'http://bave.io/',
    'images': [],
    'depends': [
        'hr',
        'hr_holidays',
        'hr_payroll',
        'btek_hr_employee_extend',
        'mail',
        'hr_payroll_account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/hr_security.xml',
        'views/payslip_detail_template.xml',
        'views/hr_public_holiday_view.xml',
        'views/hr_holiday_status_extend_view.xml',
        'data/public_holidays_data.xml',
        'data/hr_payroll_data.xml',
        'views/config_payroll_day.xml',
        'views/hr_bsc_department_view.xml',
        'views/hr_kpi_employee_view.xml',
        'views/hr_payslip_extend_view.xml',
        'views/public_holiday_calendar.xml',
        'views/payslip_template.xml',
        'views/report_payslip.xml',
        'data/resource_calender.xml',


    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
