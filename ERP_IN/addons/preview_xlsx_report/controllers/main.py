# -*- coding: utf-8 -*-
from odoo import http, _
import tempfile, os
from odoo.addons.web.controllers.main import serialize_exception,content_disposition
import base64

try:
    import openpyxl
    from xlsx2html.core import worksheet_to_data,render_data_to_html
except:
    pass


class PreviewXlsxReport(http.Controller):
    @http.route(
        ['/preview-xlsx-report/<string:file_name>/<string:report_name>'],
        auth='user', website=True)
    def main_report(self, file_name, report_name, **kw):
        file_path = os.path.join(tempfile.gettempdir(), file_name)

        sheets = []
        wb = openpyxl.load_workbook(file_path, data_only=True)

        for sheet_name in wb.get_sheet_names():
            ws = wb[sheet_name]
            data = worksheet_to_data(ws, locale='ru')
            html = render_data_to_html(data)
            sheets.append(
                {
                    'html': html,
                    'name': sheet_name
                }
            )

        datas = {
            'sheets': sheets,
            'title': '',
            'file_name': file_name,
            'report_name': _(report_name) + '.xlsx',
        }

        return http.request.render(
            'preview_xlsx_report.preview_xlsx_report_template',
            datas)

    @http.route(
        ['/download-xlsx-report/<string:file_name>/<string:report_name>'],
        auth='user', website=True)
    def download_xlsx_report(self, file_name, report_name, **kw):
        file_path = os.path.join(tempfile.gettempdir(), file_name)
        xlsx_file = open(file_path, "rb")
        filecontent = base64.b64encode(xlsx_file.read())

        content_disposition = http.content_disposition(report_name)

        headers = [('Content-Type', u'application/javascript'),
                   ('X-Content-Type-Options', 'nosniff'),
                   ('ETag', '"56d3b71b5852986e17f6edca970a84d6"'),
                   ('Cache-Control', 'max-age=0'),
                   ('Content-Disposition',
                    content_disposition
                    )]

        content_base64 = base64.b64decode(filecontent)
        headers.append(('Content-Length', len(content_base64)))

        response = http.request.make_response(content_base64, headers)
        return response
