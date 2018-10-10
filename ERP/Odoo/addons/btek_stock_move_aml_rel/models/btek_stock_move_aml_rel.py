from odoo import api, fields, models, _
import datetime


class btek_account_move_lines(models.Model):
    _inherit = 'account.move.line'

    x_stock_move_id = fields.Integer(string="Stock move id")


class btek_stock_move(models.Model):
    _inherit = "stock.move"

    def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id):
        res = super(btek_stock_move, self)._prepare_account_move_line(qty, cost,
                                                                      credit_account_id, debit_account_id)
        for line in res:
            line[2].update(x_stock_move_id=self.id)
        return res

