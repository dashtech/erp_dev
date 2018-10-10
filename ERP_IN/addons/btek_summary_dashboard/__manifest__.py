{
    "name": "Btek Summary Dashboard",
    "version": "1.0",
    "author" : 'Bave technology',
    'website' : 'http://bave.io/',
    "depends": [
        'base',
        'sale',
        'purchase',
        'car_repair_industry',
        'preview_xlsx_report',
    ],
    "category": "Report",
    "data": [
        'security/sale_report_security.xml',
        'security/ir.model.access.csv',

        'templates/summary_report.xml',
        'views/menu_view.xml',
        'views/sale_report.xml',
        'views/sale_report_to_excel.xml',
    ],
    'css': [
        'btek_summary_dashboard/static/src/css/summary_dashboard_style.css',
    ],
    'installable': True,
    'application': True,
}
