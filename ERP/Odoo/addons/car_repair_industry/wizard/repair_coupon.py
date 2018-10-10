# -*- coding: utf-8 -*-


from odoo import fields, models, api, _
from datetime import date, datetime
from odoo.exceptions import ValidationError


class FleetRepairCoupon(models.TransientModel):
    _name = 'fleet.repair.coupon'
    coupon_code = fields.Char(string='Coupon Code', required=True)

    def do_compare_coupon(self):
        if self.coupon_code:
            today = datetime.utcnow().date()
            voucher_obj = self.env['voucher.voucher'].search([('active', '=', True), ('expiry_date', '>=', today),
                                                              ('voucher_code', '=', self.coupon_code)])
            voucher_his = self.env['voucher.history']
            amount_gift = 0
            if voucher_obj:
                so_id = self.env['sale.order'].browse(self._context.get('active_id'))
                for voucher_id in voucher_obj:
                    voucher_his_used = voucher_his.search([('voucher_id', '=', voucher_id.id),
                                                           ('user_id', '=', so_id.partner_id.id)])
                    if voucher_his_used:
                        raise ValidationError(_('Used coupon code. Check again, please!'))
                    elif self.coupon_code == voucher_id.voucher_code:
                        voucher_config = self.env['voucher.config'].search([('active', '=', True),])
                        if voucher_id.applied_on == 'all':
                            if voucher_id.voucher_val_type == 'percent':
                                amount_gift = (so_id.amount_total * voucher_id.voucher_value) / 100
                            if voucher_id.voucher_val_type == 'amount':
                                amount_gift = voucher_id.voucher_value * (len(so_id.order_line) + len(so_id.order_line_service))
                        elif voucher_id.applied_on == 'order':
                            if voucher_id.voucher_val_type == 'amount':
                                amount_gift = voucher_id.voucher_value
                            if voucher_id.voucher_val_type == 'percent':
                                amount_gift = voucher_id.voucher_value/100 * so_id.amount_total
                        elif voucher_id.applied_on == 'specific':
                            if voucher_id.voucher_val_type == 'percent':
                                amount = 0
                                for so_line in so_id.order_line:
                                    if so_line.product_id.product_tmpl_id.id in voucher_id.product_ids.ids:
                                        amount += so_line.price_unit
                                for sv_line in so_id.order_line_service:
                                    if sv_line.product_id.product_tmpl_id.id in voucher_id.product_ids.ids:
                                        amount += sv_line.price_unit
                                amount_gift = (amount * voucher_id.voucher_value) / 100
                            if voucher_id.voucher_val_type == 'amount':
                                amount = 0
                                for so_line in so_id.order_line:
                                    if so_line.product_id.product_tmpl_id.id in voucher_id.product_ids.ids:
                                        amount += voucher_id.voucher_value

                                for sv_line in so_id.order_line_service:
                                    if sv_line.product_id.product_tmpl_id.id in voucher_id.product_ids.ids:
                                        amount += voucher_id.voucher_value
                                amount_gift = amount
                        so_id.write({
                            'order_line_service': [(0, 0, {
                                'product_id': voucher_config.product_id.id,
                                'product_uom_qty': 1,
                                'product_uom': voucher_config.product_id.uom_id.id,
                                'price_unit': - amount_gift,
                            })],
                            'code_used': self.coupon_code
                        })
                        voucher_his.create({
                            'name': voucher_id.name,
                            'user_id': so_id.partner_id.id,
                            'voucher_value': amount_gift,
                            'voucher_id': voucher_id.id,
                            'channel_used': 'sale',
                            'order_id': so_id.id,
                        })
                return True
            else:
                raise ValidationError(_('Invalid coupon code. Check again, please!'))
        return {'type': 'ir.actions.act_window_close'}


class VoucherVoucherInherit(models.Model):
    _inherit = 'voucher.voucher'

    applied_on = fields.Selection(selection_add=[('order', _('Orders'))])
