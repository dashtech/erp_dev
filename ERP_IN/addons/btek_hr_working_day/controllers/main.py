# -*- coding: utf-8 -*-
from odoo import http, SUPERUSER_ID
from odoo.http import Controller, Response, request, route
from datetime import datetime, timedelta


class HrWorkingDay(http.Controller):

    @http.route(['/api/timesheet_unlink'], type='json', auth="public", methods=['POST'], website=True)
    def _unlink_timesheet(self, **post):

        if post.get('employee_id'):
            date_from = datetime.strptime(post.get('date_from'), '%Y-%m-%d %H:%M:%S') + timedelta(hours=7)
            date_to = datetime.strptime(post.get('date_to'), '%Y-%m-%d %H:%M:%S') + timedelta(hours=7)
            real_date_from = datetime.strftime(date_from, '%Y-%m-%d')
            real_date_to = datetime.strftime(date_to, '%Y-%m-%d')
            emp_line_ids = request.env['hr.working.day.employee.line'].search([('employee_id', '=', int(post.get('employee_id'))),
                                                                               ('date', '>=', real_date_from),
                                                                               ('date', '<=', real_date_to)])
            if emp_line_ids:
                [line.unlink() for line in emp_line_ids]
        return True

    @http.route(['/api/timesheet_autofill'], type='json', auth="public", methods=['POST'], website=True)
    def _timesheet_autofill(self, **post):
        worked_employee = []
        if post.get('emp_id'):
            employee_id = post.get('emp_id')
            date_from = datetime.strptime(post.get('date_from'), '%Y-%m-%d %H:%M:%S') + timedelta(hours=7)
            date_to = datetime.strptime(post.get('date_to'), '%Y-%m-%d %H:%M:%S') + timedelta(hours=7)
            count_day = (date_to - date_from).days
            real_date_from = datetime.strftime(date_from, '%Y-%m-%d')
            real_date_to = datetime.strftime(date_to, '%Y-%m-%d')

            works = request.env['hr.working.day.employee'].sudo().search([('employee_id', '=', employee_id),
                                                                          ('date', '>=', real_date_from),
                                                                          ('date', '<=', real_date_to)])
            if not works:
                flag = 0
                for i in range(count_day+1):
                    date_count = datetime.strftime((date_from + timedelta(days=i)), '%Y-%m-%d')
                    holiday = request.env['hr.holidays'].sudo().search([('employee_id', '=', employee_id),
                                                                        ('day_ez', '=', date_count),
                                                                        ('state', '=', 'validate')])
                    public_holiday = request.env['btek.hr.public.holiday.line'].sudo().search([('date', '=', date_count)])
                    if holiday:
                        flag = holiday.number_of_days_temp
                        if holiday.number_of_days_temp == 1:
                            work_dct = ({
                                'date': date_count,
                                'unit_amount': 0,
                                'name': '/',
                                'employee_id': employee_id,
                            })
                            worked_employee.append(work_dct)
                            flag -= 1
                            continue
                        if holiday.number_of_days_temp < 1:
                            work_dct = ({
                                'date': date_count,
                                'unit_amount': (1 - holiday.number_of_days_temp),
                                'name': '/',
                                'employee_id': employee_id,
                            })
                            worked_employee.append(work_dct)
                            continue
                    if flag > 0:
                        work_dct = ({
                            'date': date_count,
                            'unit_amount': 0,
                            'name': '/',
                            'employee_id': employee_id,
                        })
                        worked_employee.append(work_dct)
                        flag -= 1
                        continue
                    if public_holiday:
                        work_dct = ({
                            'date': date_count,
                            'unit_amount': 0,
                            'name': '/',
                            'employee_id': employee_id,
                        })
                        worked_employee.append(work_dct)
                        continue
                    if not holiday and flag == 0:
                        work_dct = ({
                            'date': date_count,
                            'unit_amount': 1,
                            'name': '/',
                            'employee_id': employee_id,
                        })
                        worked_employee.append(work_dct)
                        continue

            else:
                for work in works:
                    public_holiday = request.env['btek.hr.public.holiday.line'].sudo().search(
                        [('date', '=', work.date)])
                    if public_holiday:
                        work_dct = ({
                            'date': work.date,
                            'unit_amount': 0,
                            'name': '/',
                            'employee_id': employee_id,
                        })
                        worked_employee.append(work_dct)
                    else:
                        work_dct = ({
                            'date': work.date,
                            'unit_amount': work.unit_amount,
                            'name': '/',
                            'employee_id': employee_id,
                        })
                        worked_employee.append(work_dct)
            return worked_employee
