# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError


class HrEmployeeExtend(models.Model):
    _inherit = 'hr.employee'

    related_person_ids = fields.One2many('btek.related.person',
                                         'employee_id', string=u'Người phụ thuộc')
    related_child_ids = fields.One2many('btek.related.child',
                                        'employee_id')
    children = fields.Integer(string=u'Số con', groups='hr.group_hr_user',
                              compute = '_compute_child')
    related_person = fields.Integer(string=u'Số người phụ thuộc',
                                    groups='hr.group_hr_user',
                                    compute = '_compute_person')
    allow_timesheets = fields.Boolean("Allow timesheets", default=True)
    code_name = fields.Char(u'Tên viết tắt')
    home_addr = fields.Char('Home address')
    id_date = fields.Date('Date approve')
    id_location = fields.Char('Location approve')
    related_person_payslip = fields.Integer()

    @api.multi
    @api.depends('related_child_ids')
    def _compute_child(self):
        for s in self:
            related_child_ids = s.related_child_ids
            s.children = len(related_child_ids)
        return True

    @api.multi
    @api.depends('related_person_ids')
    def _compute_person(self):
        for s in self:
            s.related_person = len(s.related_person_ids)
        return True

    @api.model
    def create(self, vals):
        res = super(HrEmployeeExtend, self).create(vals)
        if vals.has_key('code_name'):
            check_code_name = self.env['hr.employee'].sudo().search(
                [('code_name', '=', vals['code_name'])])
            if len(check_code_name) > 1:
                raise ValidationError(u'Tên viết tắt phải là duy nhất!')
        return res

    @api.multi
    def write(self, vals):
        res = super(HrEmployeeExtend, self).write(vals)
        if vals.has_key('code_name'):
            check_code_name = self.env['hr.employee'].sudo().search(
                [('code_name', '=', vals['code_name'])])
            if len(check_code_name) > 1:
                raise ValidationError(u'Tên viết tắt phải là duy nhất!')
        return res

    #overwrite function base
    @api.multi
    def _inverse_manual_attendance(self):
        manual_attendance_group = self.env.ref('hr.group_hr_attendance').sudo()
        for employee in self:
            if employee.user_id:
                if employee.manual_attendance:
                    manual_attendance_group.users = [(4, employee.user_id.id, 0)]
                else:
                    manual_attendance_group.users = [(3, employee.user_id.id, 0)]
        return True


class HrContractConfig(models.Model):
    _name = 'hr.contract.config'

    name = fields.Char(default='Base Salary Insurance')
    insurance_salary_base = fields.Float('Base Salary Insurance')

    def set_base_ins(self):
        contracts = self.env['hr.contract'].search([])
        val = {'insurance_salary': self.insurance_salary_base}
        res = contracts.write(val)
        return res


class HrContractInherit(models.Model):
    _inherit = 'hr.contract'

    def default_insurance(self):
        insurance_salary = self.env['hr.contract.config'].search([],limit=1,order='id')
        if not insurance_salary:
            ins_salary = 4300000
            return ins_salary
        ins_salary = insurance_salary.insurance_salary_base
        return ins_salary

    company_id = fields.Many2one('res.company', related='department_id.company_id', store=True)
    insurance_salary = fields.Float('Base Salary Insurance', default=default_insurance)
    addition_salary_non = fields.Float('Addition Salary')


class PartnerBankInherit(models.Model):
    _inherit = 'res.partner.bank'

    name = fields.Char()

