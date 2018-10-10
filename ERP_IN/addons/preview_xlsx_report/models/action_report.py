# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import datetime
import os, tempfile

class  ir_actions_report_xml(models.Model):
    _inherit = 'ir.actions.report.xml'

    def preview_xlsx_report(self, report_name, res_ids, report_datas):
        self.env.cr.execute(
            "SELECT * FROM ir_act_report_xml WHERE report_name=%s",
            (report_name,))
        row = self.env.cr.dictfetchone()
        if not row:
            return 'Unsupported this report!'

        if row['report_type'] != 'xlsx':
            return 'Unsupported {} report type!'.format(row['report_type'])

        report_obj = self.env['ir.actions.report.xml']

        result = report_obj.render_report(
            res_ids, report_name, report_datas)

        # report_data = result.decode('base64')
        report_data = result

        file_name = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S') + \
               '_' + str(self.env.user.id) + \
               'preview_xlsx_report.xlsx'

        file_path = os.path.join(tempfile.gettempdir(), file_name)

        if isinstance(report_data, (list, tuple)):
            if len(report_data):
                report_data = report_data[0]

        f = open(file_path, "wb")
        f.write(report_data)
        f.close()

        url = u'''/preview-xlsx-report/{}/{}'''.format(file_name, row['name'])
        return {
            'type': 'ir.actions.act_url',
            'url': url,
        }


