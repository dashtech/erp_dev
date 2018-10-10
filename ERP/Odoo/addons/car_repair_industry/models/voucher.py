from odoo import fields, models, api


class VoucherHistory(models.Model):
    _inherit = "voucher.history"

    channel_used = fields.Selection([('pos', 'POS'),
                                    ('e-commerce', 'E-commerce'),
                                    ('sale', 'Sales'),
                                    ('both', 'Other')],
                                    required=True, string="Channel", help="Channel by which voucher has been used.")


class LoyaltyHistory(models.Model):
    _inherit = "pos.loyalty.history"
    _rec_name = 'order_id'

    source = fields.Selection([('pos', 'Point of Sale'),
                               ('sale', 'Sale Order'),
                               ('website', 'Website')], string="Source", default='pos')
    order_id = fields.Many2one('sale.order', string="Order Reference")
    amount_pay = fields.Float('Amount Pay')
