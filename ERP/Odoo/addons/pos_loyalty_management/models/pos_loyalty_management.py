# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
#################################################################################
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class PosCategory(models.Model):
    _inherit = 'pos.category'

    wk_point_for_loyalty = fields.Integer(string='Loyalty Points', help="How many loyalty points are given to the customer by product sold under this category.")

    @api.one
    @api.constrains('wk_point_for_loyalty')
    def set_point_for_loyalty_for_child(self):
        for self_obj in self:
            categories_objs = self_obj.search([])
            for obj in categories_objs:
                if obj.parent_id.id == self_obj.id:
                    if  obj.wk_point_for_loyalty == 0:
                        obj.wk_point_for_loyalty = self_obj.wk_point_for_loyalty

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    wk_point_for_loyalty = fields.Integer(related='pos_categ_id.wk_point_for_loyalty', string='Loyalty Points',
                                          help="How many loyalty points are given to the customer by product sold.", readonly=True)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    wk_loyalty_points = fields.Integer(string='Loyalty Points', help='The loyalty points the user won as part of a Loyalty Program')


class LoyaltyManagement(models.Model):
    _name = 'loyalty.management'
    _description = "POS loyalty Configration"

    def _default_loyalty_product(self):
        ir_model_data = self.env['ir.model.data']
        product_id = False
        try:
            product_id = ir_model_data.get_object_reference('pos_loyalty_management', 'wk_loyalty_product_id')[1]
        except ValueError:
            product_id = False
        return product_id

    name = fields.Char(string='Name', size=100, default=lambda self: _('/'))
    start_date = fields.Datetime(string='Start Date', default=fields.Datetime.now)
    end_date = fields.Datetime(string='End Date')
    redeem_rule_list = fields.Many2many('redeem.rule.list', 'rule11', 'rule22', 'rule33', string='Redemption Rule List')
    minimum_purchase = fields.Float(string='Minimum Purchase amount for which the points can be awarded', help="Minimum Purchase amount for which the points can be awarded.")

    # active = fields.Boolean(string='Active', default=True)
    config_active = fields.Boolean(string='Active', default=True)

    points = fields.Integer(string='Points')
    purchase = fields.Float(string='Purchase')
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, help="Currency of your Company.", default=lambda self: self.env.user.company_id.currency_id.id)

    loyality_product_id = fields.Many2one('product.product', string='Loyalty Product', domain=[('sale_ok', '=', True), ('available_in_pos', '=', True)], help="This Product is used as a Loyalty Product.", default=_default_loyalty_product)

    loyalty_base = fields.Selection([('amount', 'Purchase Amount'),
                                     ('category', 'POS Product Categories')
                                     ], string='On the Basis', required=True, default='category')

    @api.model
    def create(self, vals):
        if vals.get('config_active'):
            if len(self.search([('config_active', '=', True)])) >= 1:
                raise UserError(_("Sorry, Only one active configuration is allowed."))
        if vals:
            redeem_rule_list_ids = vals.get('redeem_rule_list')
            if redeem_rule_list_ids:
                redeem_list = redeem_rule_list_ids[0][2]
                redeem_rule_objs = self.redeem_rule_list.search([('id','in',redeem_list)])
                for index in range(0,len(redeem_list)-1):
                    for sibling_index in range(index+1,len(redeem_list)):
                        points_ub = redeem_rule_objs[index].points_to
                        points_lb = redeem_rule_objs[index].points_from
                        sibling_ub = redeem_rule_objs[sibling_index].points_to
                        sibling_lb = redeem_rule_objs[sibling_index].points_from
                        if((points_lb >= sibling_lb and points_lb < sibling_ub) or (points_ub > sibling_lb and points_ub <= sibling_ub)) :       
                            raise ValidationError("There is some overlapping in Redemption Rule List Range. Please check and re-assign range again.")
                        elif((sibling_lb >= points_lb and sibling_lb < points_ub) or (sibling_ub > points_lb and sibling_ub <= points_ub)):
                           raise ValidationError("There is some overlapping in Redemption Rule List Range. Please check and assig points range again.")
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('loyalty.management')
        return super(LoyaltyManagement, self).create(vals)

    @api.one
    @api.constrains('start_date','end_date')
    def date_validation_check(self):
        if self.start_date:
            if self.end_date:
                if(self.start_date > self.end_date):
                    raise ValidationError("End date must be greater than start date")

    @api.one
    @api.constrains('minimum_purchase','purchase','points')
    def negative_value_check(self):
        if self.minimum_purchase < 0 :
            raise ValidationError("Minimum purchase value must be greater than or equals to zero")

        if self.points < 0 :
            raise ValidationError("Points must be greater than equal to zero")
        
        if self.purchase < 0 :
            raise ValidationError("Purchase must be greater than equal to zero")

    @api.multi
    def write(self, vals):
        if vals.get('config_active'):
            if len(self.search([('config_active', '=', True)])) >= 1:
                raise UserError(_("Sorry, Only one active configuration is allowed."))
        if vals:
            redeem_rule_list_ids = vals.get('redeem_rule_list')
            if redeem_rule_list_ids:
                redeem_list = redeem_rule_list_ids[0][2]
                redeem_rule_objs = self.redeem_rule_list.search([('id','in',redeem_list)])
                for index in range(0,len(redeem_list)-1):
                    for sibling_index in range(index+1,len(redeem_list)):
                        points_ub = redeem_rule_objs[index].points_to
                        points_lb = redeem_rule_objs[index].points_from
                        sibling_ub = redeem_rule_objs[sibling_index].points_to
                        sibling_lb = redeem_rule_objs[sibling_index].points_from
                        if((points_lb >= sibling_lb and points_lb < sibling_ub) or (points_ub > sibling_lb and points_ub <= sibling_ub)) :       
                            raise ValidationError("There is some overlapping in Redemption Rule List Range. Please check and assig points range again.")
                        elif((sibling_lb >= points_lb and sibling_lb < points_ub) or (sibling_ub > points_lb and sibling_ub <= points_ub)):
                           raise ValidationError("There is some overlapping in Redemption Rule List Range. Please check and assig points range again.")
       
        return super(LoyaltyManagement, self).write(vals)

    @api.model
    def get_customer_loyality(self, customer_id, total_amount):
        remaining_points = 0
        if customer_id:
            loyality_points = self.env["res.partner"].browse(customer_id).wk_loyalty_points
            loyalty_object = self.search([('config_active', '=', True)])
            if loyalty_object:
                discount = loyalty_object.with_context(loyality_points=loyality_points).get_discount()
            if discount['line_discount']:
                remaining_points = float(
                    discount['total_discount'] - total_amount) / discount['line_discount']
                if remaining_points < 0:
                    remaining_points = 0
            return {'discount': discount['total_discount'], 'points': loyality_points, 'customer': customer_id, 'remaining_points': remaining_points}
        else:
            return {'discount': 0, 'points': 0, 'customer': 0, 'remaining_points': 0}

    @api.model
    def get_loyalty_product(self):
        loyalty_object = self.search([('config_active', '=', True)])
        if loyalty_object:          
            if (loyalty_object.end_date and datetime.now() > datetime.strptime(loyalty_object.end_date, "%Y-%m-%d %H:%M:%S")):
                loyalty_object.write({'config_active':False})
                return False
            return loyalty_object[0].loyality_product_id.id
        return False

    def get_discount(self):
        total_discount, line_discount = 0, 0
        loyality_points = self._context['loyality_points'] if self._context.get('loyality_points') else 0
        for line in self.redeem_rule_list:
            points_to = line.points_to
            points_from = line.points_from
            if (loyality_points >= points_from and loyality_points <= points_to):
                total_discount = loyality_points * line.discount
                line_discount = line.discount
        if not self.redeem_rule_list:
            total_discount = -1
        return {'total_discount': total_discount, 'line_discount': line_discount}


class RedeemRuleList(models.Model):
    _name = 'redeem.rule.list'

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            currency = self.env['res.currency'].browse(vals.get('currency_id'))
            vals['name'] = "Rule : " + str(vals.get('points')) + " loyalty points, can be redeem to a discount of " + str(
                vals.get('discount')) + " " + str(currency.name_get()[0][1])
        return super(RedeemRuleList, self).create(vals)

    name = fields.Char(string='Name', size=100, readonly=True, default=lambda self: '/')
    rule_name = fields.Char(string='Rule Name', size=100)

    # active = fields.Boolean(string='Active', default=True)
    config_active = fields.Boolean(string='Active', default=True)
    active_rule = fields.Boolean(string="Active Rule", default=True)
    
    points_from = fields.Integer(string='Loyality Points', required=True)
    points_to = fields.Integer(string='Loyality Points', required=True)
    discount = fields.Float(string='Discount', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, help="Currency of your Company.", default=lambda self: self.env.user.company_id.currency_id.id)

    @api.one
    @api.constrains('points_from','points_to','discount')
    def point_range_validation(self):
        if(self.points_from < 0 or self.points_to < 0):
            raise ValidationError("Points range must be positve integer type.")
        if(self.discount <= 0):
            raise ValidationError("Discount must be greater than zero.")
        if(self.points_from > self.points_to):
            raise ValidationError("In Redemption Rule List, starting point must be less than ending point") 
      
class PosOrder(models.Model):
    _inherit = "pos.order"

    wk_loyalty_points = fields.Float(string='Loyalty Points', help='The amount of Loyalty points the customer won or lost with this order')

    @api.model
    def _order_fields(self, ui_order):
        fields = super(PosOrder, self)._order_fields(ui_order)
        fields['wk_loyalty_points'] = ui_order.get('wk_loyalty_points')
        return fields

    @api.model
    def create_from_ui(self, orders):
        values = {}
        ids = super(PosOrder, self).create_from_ui(orders)
        for order in orders:
            if order['data']['wk_loyalty_points'] and order['data']['partner_id']:
                partner = self.env['res.partner'].browse(order['data']['partner_id'])
                values.update({'pos_order_id': order['data']['lines'][0][2]['order_id'],
                               'session_id': order['data']['pos_session_id'],
                               'customer_id': order['data']['partner_id'],
                               'salesman_id': order['data']['user_id'],
                               'tx_date': order['data']['creation_date'],
                               })
                if order['data']['redeemTaken']:
                    remaining_points = order['data']['wk_loyalty_points']
                    values['tx_type'] = 'debit'
                    values['tx_points'] = abs(partner.wk_loyalty_points - order['data']['wk_loyalty_points'])
                else:
                    remaining_points = partner.wk_loyalty_points + order['data']['wk_loyalty_points']
                    values['tx_type'] = 'credit'
                    values['tx_points'] = order['data']['wk_loyalty_points']
                partner.sudo().write({'wk_loyalty_points': remaining_points})
                values['remain_points'] = remaining_points
                self.create_loyalty_history(values)
            if order['data']['wk_loyalty_points'] == 0 and order['data']['partner_id']:
                if order['data']['redeemTaken']:
                    partner = self.env['res.partner'].browse(order['data']['partner_id'])
                    remaining_points = order['data']['wk_loyalty_points']
                    partner.sudo().write({'wk_loyalty_points': remaining_points})
        return ids

    def create_loyalty_history(self, vals):
        try:
            history_obj = self.env['pos.loyalty.history']
            history_obj.create(vals)
        except Exception, e:
            return False
