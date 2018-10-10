# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError
import datetime


class WizardMakeConsignmentPOLine(models.TransientModel):
    _name = 'make.consignment.po.line'

    @api.multi
    def _compute_show_all_partner(self):
        for wizard in self:
            len_partner_ids = len(wizard.partner_ids)
            show_all_partner = True
            if len_partner_ids:
                show_all_partner = False
            wizard.show_all_partner = show_all_partner

    wizard_id = fields.Many2one('make.consignment.po', required=True)
    order_line_id = fields.Many2one('sale.order.line', required=True)
    product_id = fields.Many2one('product.product',
                                 related='order_line_id.product_id',
                                 string='Product', readonly=True)
    product_uom_qty = fields.Float(string='Order qty',
                                   related='order_line_id.product_uom_qty',
                                   readonly=True)
    product_qty = fields.Float('Purchase qty')
    price_unit = fields.Float('Price unit')
    partner_ids = fields.Many2many('res.partner', string='Supplier',
                                 readonly=True)
    partner_id = fields.Many2one('res.partner', 'Supplier')
    show_all_partner = fields.Boolean(
        compute='_compute_show_all_partner')

    def prepare_wizard_line_to_po_line(self):
        res = {
            'product_id': self.product_id.id,
            'name': self.product_id.name,
            'product_uom': self.product_id.uom_po_id.id,
            'price_unit': self.price_unit,
            'product_qty': self.product_qty,
            'date_planned': datetime.datetime.now(),
        }
        return res

class WizardMakeConsignmentPO(models.TransientModel):
    _name = 'make.consignment.po'

    order_id = fields.Many2one('sale.order', 'Order',
                               required=True)
    line_ids = fields.One2many('make.consignment.po.line',
                               'wizard_id', 'Lines')
    # type_id = fields.Many2one('stock.picking.type',
    #                           'Stock picking type',
    #                           required=True)

    @api.model
    def find_stock_picking_type(self):
        src_location_ids = \
            self.env['stock.location'].search(
                [('consignment', '=', True),
                 ('company_id', '=', self.env.user.company_id.id)]
            )
        if not src_location_ids:
            raise UserError(
                _('Error: Cannot find consignment location!'))

        src_location_id = src_location_ids[0].id

        type_ids = self.env['stock.picking.type'].search(
            [('default_location_src_id', '=', src_location_id)]
        )
        type = type_ids and type_ids[0] or False
        if not type:
            raise UserError(
                _('Error: invalid config picking type!')
            )

        return type


    @api.multi
    def make_po(self):
        partner_dict = {}
        for line in self[0].line_ids:
            if not line.partner_id:
                raise UserError(
                    _('Error: you have to enter the full supplier before!'))

            partner_id = line.partner_id.id
            if not partner_dict.get(partner_id, False):
                partner_dict[partner_id] = []

            partner_dict[partner_id].append(
                line.prepare_wizard_line_to_po_line())

        type = self.find_stock_picking_type()

        po_ids = []

        for partner_id in partner_dict.keys():
            vals = {
                'partner_id': partner_id,
                'consignment': True,
                'picking_type_id': type.id,
                'order_line': [(0, 0, line_vals)
                               for line_vals in partner_dict[partner_id]]
            }
            po = self.env['purchase.order'].create(vals)
            po.button_confirm()
            for picking in po.picking_ids:
                transfer = picking.do_new_transfer()
                wiz_id = transfer['res_id']
                wiz = self.env['stock.immediate.transfer'].browse(wiz_id)
                wiz.process()

            po_ids.append(po.id)
        self[0].order_id.write({
            'consignment_po_ids': [(6, False, po_ids)]
        })

        return True


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    consignment = fields.Boolean(default=False)
    consignment_po_ids = fields.Many2many(
        'purchase.order',
        'sale_order_consignment_purchase_order_rel',
        'sale_order_id', 'purchase_order_id',
        string='Consignment purchase order',
        readonly=True, copy=False)

    @api.multi
    def open_create_consignment_po(self):
        order = self[0]
        line_ids = []

        for line in order.order_line:
            # if not line.product_id.consignment:
            #     continue

            # if not line.product_id.seller_ids:
            #     raise UserError(
            #         _('Error: product {} has no supplier!').format(
            #             line.product_id.name))

            partner_ids = [p.name.id for p in line.product_id.seller_ids]

            line_vals = {
                'order_line_id': line.id,
                'product_qty': line.product_uom_qty,
                'partner_id': partner_ids and partner_ids[0] or False,
                'partner_ids': [(6, False, partner_ids)]
            }
            line_ids.append((0, 0, line_vals))

        if not line_ids:
            raise UserError(
                _('Error: order has no consignment product!'))

        vals = {
            'line_ids': line_ids,
            'order_id': order.id,
        }

        wizard_id = self.env['make.consignment.po'].create(vals)

        action_obj = self.env.ref(
            'btek_sale.action_make_consignment_po_form')
        action = action_obj.read()[0]
        action['res_id'] = wizard_id.id

        return action

    @api.multi
    def make_invoice_automatic(self):
        if self[0].state != 'sale':
            raise UserError('Error: You must confirm order before!')

        wizard_obj = \
            self.env['sale.advance.payment.inv'].with_context(
                active_model='sale.order',
                active_ids=self._ids,
                active_id=self._ids[0],
            )

        product = wizard_obj._default_product_id()
        product_id = product.id or False

        deposit_account = wizard_obj._default_deposit_account_id()
        deposit_account_id = deposit_account.id

        deposit_taxes = wizard_obj._default_deposit_taxes_id()
        deposit_taxes_id = deposit_taxes and deposit_taxes.mapped('id') or False

        wizard_vals = {
            'deposit_account_id': deposit_account_id,
            'advance_payment_method': wizard_obj._get_advance_payment_method(),
            'product_id':  product_id,
            'deposit_taxes_id': deposit_taxes_id,
        }
        wizard = wizard_obj.create(wizard_vals)
        res = wizard.with_context(
                active_model='sale.order',
                active_ids=self._ids,
                active_id=self._ids[0],
            ).create_invoices()
        return True

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    invoice_confirmed = fields.Boolean(
        compute='_compute_invoice_confirmed',
        store=True)
    invoice_state = fields.Selection(
        [('open', 'Confirmed'),
         ('paid', 'Paid')],
        compute='_compute_invoice_state',
        store=True
    )

    @api.depends('invoice_lines.invoice_id.state')
    @api.multi
    def _compute_invoice_state(self):
        for line in self:
            line.invoice_state = 'paid'
            state_list = line.order_id.invoice_ids.mapped('state')
            if not state_list:
                line.invoice_state = 'open'
                continue

            if any(state != 'paid' for state in state_list):
                line.invoice_state = 'open'

    @api.depends('invoice_lines.invoice_id.state')
    @api.multi
    def _compute_invoice_confirmed(self):
        for line in self:
            line.invoice_confirmed = True
            state_list = line.order_id.invoice_ids.mapped('state')
            if not state_list:
                line.invoice_confirmed = False
                continue

            for state in state_list:
                if state not in ('open', 'paid'):
                    line.invoice_confirmed = False
                    break

    @api.onchange('discount')
    def onchange_discount(self):
        if self.discount and self.discount > 100:
            self.discount = 0.0
            title = _("Warning for discount")
            message = _('Discount greater 100%')
            warning = {
                'title': title,
                'message': message,
            }
            return {'warning': warning}


