from odoo import fields, models, api


class SurveyLabel(models.Model):
    _inherit = "survey.label"

    color = fields.Selection(string="Color", selection=[('radio-primary', 'Primary'),
                                                        ('radio-danger', 'Danger'),
                                                        ('radio-info', 'Info'),
                                                        ('radio-warning', 'Warning'),
                                                        ('radio-success', 'Success')], default="radio-success")


SurveyLabel()


class SurveyQuestion(models.Model):
    _inherit = "survey.question"

    # type = fields.Selection(selection_add=[('matrix_input', 'Matrix Input')])
    group = fields.Selection(

        [('default', 'Default'),
         ('paint', 'Paint type'),
         ('tire', 'Tire type'),
         ('gas', 'Gas'),
         ('axit', 'Axit'),
         ('battery', 'Battery'),
         ('tire_size', 'Tire size'),
         ],
        default='default', string='Group',
        required=True)
    product_ids = fields.Many2many('product.product',
                                   'survey_question_product_product_rel',
                                   'question_id', 'product_id',
                                   string='Suggest products')

    type = fields.Selection([
        ('free_text', 'Multiple Lines Text Box'),
        ('textbox', 'Single Line Text Box'),
        ('numerical_box', 'Numerical Value'),
        # ('datetime', 'Date and Time'),
        ('simple_choice', 'Multiple choice: only one answer'),
        ('multiple_choice', 'Multiple choice: multiple answers allowed'),
        ('matrix_input', 'Matrix Input'),
        ('matrix_row', 'Row Matrix')], string='Type of Question', default='matrix_input', required=True)

SurveyQuestion()
