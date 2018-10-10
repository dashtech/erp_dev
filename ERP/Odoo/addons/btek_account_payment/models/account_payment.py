# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountPaymentInherit(models.Model):
    _inherit = 'account.payment'

    @api.multi
    def post(self):
        for s in self:
            residual_total = sum([i.residual for i in s.invoice_ids])
            if not s.amount <= residual_total:
                raise UserError(_('Amount payment can not large amount total invoice'))
        return super(AccountPaymentInherit, self).post()
