from odoo import models, fields, api, _
from odoo.exceptions import UserError,Warning
from datetime import timedelta,datetime



class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    promotion_id = fields.Many2one("promotion.method", string="Promotion Method")
    coupon_code=fields.Char("Coupon Code",help="Add coupon code to apply promotion in sale order")
    promo_price=fields.Float(compute="_amount_all",string="Promotion Amount")
    
    @api.onchange('partner_id','order_line','order_line.product_id')
    def onchange_promotion_order_line(self):
        '''
            This Onchnage use for remove promotion.
        '''
        for order in self:
            order.with_context(promotion=True).write({'promotion_id':False})  
            for line in order.order_line:
                line.write({'promotion_price':0.0})
                if line.is_promotion:
                    line.write({'price_unit':0.0,'product_uom_qty':0.0})
        return {}        
    
    @api.multi
    def write(self,values):
        res=super(SaleOrder,self).write(values)
        if self._context.get('promotion'):
            res=super(SaleOrder,self).write(values)
        else:
            for line in self.order_line:
                if line.is_promotion==True and line.price_unit==0.0:
                    line.unlink()
        return res
        
    
    @api.depends('order_line.price_total')
    def _amount_all(self):
        '''
            This method use for recalculate untax amount,tax,total and add promo amount to order.
        '''
        super(SaleOrder,self)._amount_all()
        for order in self:
            discount=0.0
            amount_untaxed = promo_price = 0.0
            for line in order.order_line:
                if not line.price_subtotal<0.0:
                    amount_untaxed += line.price_subtotal
                if line.is_promotion:
                    promo_price = line.price_subtotal
                if not line.is_promotion and line.price_subtotal<0.0:
                    discount=discount+line.price_subtotal
            amount_tax=order.amount_tax
            order.update({
                'amount_untaxed': order.pricelist_id.currency_id.round(amount_untaxed),
                'promo_price': order.pricelist_id.currency_id.round(promo_price),
                'amount_total': amount_untaxed + amount_tax + promo_price + discount
            })       
    
    @api.multi
    def find_promo(self):
        self._promotion_unset()
        promotion = self.env['promotion.method'].sudo().search([('coupon_code', '=', self.coupon_code)])
        if promotion:
            self.apply_promotion(promotion)
        else:
            self.message_post(body=("<b>Coupon Code Does not match to any promotion.</b>"))
    
    @api.multi        
    def unset_promotion(self):  
        self._promotion_unset()  
        self.write({'coupon_code':''})    
    @api.multi
    def _promotion_unset(self):
        '''
            This method use for remove promotion.
        '''
        self.env['sale.order'].search([('id','in',self.ids)]).write({'promotion_id':False,'promo_price':0.0})
        self.env['sale.order.line'].search([('order_id', 'in', self.ids),('is_promotion', '=', True)]).unlink()
        self.env['sale.order.line'].search([('order_id','in', self.ids)]).write({'promotion_price':0.0})
  
    @api.multi
    def apply_promotion(self,promotion):
        '''
            This method use for apply promotion.
        '''
        for order in self:
            
                order.promotion_id=promotion
                order.set_saleorderline()
                if order.order_line:
                    price_unit=promotion.set_promotion(order,promotion,other_promotion=False)
                    if price_unit<0.0:
                        if -(price_unit)<=order.amount_untaxed or promotion.compute_price=='bogo_sale':
                            price=-(price_unit)
                            if promotion.max_promotion_amount!=0.0 and price>=promotion.max_promotion_amount:
                                price_unit=order.update_orderline_promotionprice(price,promotion.max_promotion_amount)
                                res=order._create_promotion_line(promotion, price_unit)
                                order.message_post(body=("<b>Promotion applied successfully</b>"))
                                return True
                            else:
                                res=order._create_promotion_line(promotion, price_unit)
                                order.message_post(body=("<b>Promotion applied successfully</b>"))
                                return True
                        else:
                            order._promotion_unset()
                            order.message_post(body=("<b>Order amount is less than Discount</b>"))
                            return False
                    else:
                        order._promotion_unset()
                        return False
                else:
                    order._promotion_unset()
                    order.message_post(body=("<b>Order not Contain Promotion Criteria product.</b>"))
                    #raise Warning(_('Coupon not in use.'))
        
    
    def set_saleorderline(self):
            '''
                This method use for merge orderline which contains same product in different line.
            '''
            finalids=[]
            promo=self.promotion_id
            for line in self.order_line:
                count=0.0
                ids=[]
                orderline=self.env['sale.order.line'].search([('order_id','=',self.id),('product_id','=',line.product_id.id),('product_uom','=',line.product_uom.id),('discount','=',line.discount)])
                for ol in orderline:
                    count+=1
                    if count>1:
                        line.write({'product_uom_qty':line.product_uom_qty+ol.product_uom_qty})
                        ids.insert(0, ol.id)
                for id in ids:
                    if id not in finalids:
                        finalids.append(id)
            for id in finalids:
                line=self.env['sale.order.line'].search([('id','=',id)])
                self.promotion_id=False
                line.unlink()
            self.promotion_id=promo
            
    '''@api.multi
    def action_cancel(self):
        for order in self:
            if order.promotion_id:
                order.write({'promotion_id':False,'promotion_amount':0.0})
                for orderline in order.order_line:
                    if orderline.is_promotion:
                        orderline.write({'product_uom_qty':0.0})
                        orderline.unlink()
        res=super(SaleOrder,self).action_cancel()
        return res'''
    @api.multi
    def action_confirm(self):
        '''
            This method use for reapply promotion and if it not applied then giv pop-message for remove promotion first.
        '''
        for order in self:
            promo = order.promotion_id
            if promo:
                order._promotion_unset()
                order.promotion_id=promo
                promotion=order.promotion_id
                price_unit=promotion.set_promotion(order,promotion,other_promotion=False)
                if price_unit<0.0:
                    if -(price_unit)<=order.amount_untaxed or promotion.compute_price=='bogo_sale':
                        price=-(price_unit)
                        if promotion.max_promotion_amount!=0.0 and price>=promotion.max_promotion_amount:
                            price_unit=self.update_orderline_promotionprice(price,promotion.max_promotion_amount)
                            res=self._create_promotion_line(promotion, price_unit)
                            order.message_post(body=("<b>Order Confirmed and Promotion applied successfully.</b>"))
                        else:
                            res=self._create_promotion_line(promotion, price_unit)
                            order.message_post(body=("<b>Order Confirmed and Promotion applied successfully.</b>"))
                    else:
                        raise UserError(_("Promotion is not apply in your order please remove Promotion and then Confirm order."))
                else:
                    raise UserError(_("Promotion is not apply in your order please remove promo code and Confirm order."))
        res=super(SaleOrder,self).action_confirm()
        return res
    
    def update_orderline_promotionprice(self,price,max_promotion_price):
        '''
            This method is use when promotion price is greter then max promotion.
        '''
        price_unit=0.0
        for line in self.order_line:
            ratio=max_promotion_price/price
            if line.promotion_price!=0.0:
                line_price=line.promotion_price*ratio
                line.write({'promotion_price':line_price})
                price_unit+=line_price
        return price_unit
        
    
    def _create_promotion_line(self, promotion, price_unit):
        '''
            This method use for add promotionline in order.
        '''
        SaleOrderLine = self.env['sale.order.line']
        # Create the sale order line
        if promotion.bogo_sale_on in ['bxgy']:
            sol=SaleOrderLine.search([('order_id','=',self.id),('promotion_product','=',True)])
            for line in sol:
                qty=line.product_uom_qty
                free_qty=qty/promotion.bxgy_Aproduct_unit
                price_unit=price_unit*int(free_qty)
                line.write({'promotion_product':False,'promotion_price':0.0})
                name = line.product_id.name_get()[0][1]
                if line.product_id.description_sale:
                    name += '\n' + line.product_id.description_sale
                if line:
                    values = {
                    'order_id': self.id,
                    'name': name,
                    'product_uom_qty': int(free_qty)*promotion.bxgy_Bproduct_unit,
                    'product_uom': line.product_id.uom_id.id,
                    'product_id':line.product_id.id,
                    'price_unit': line.price_unit,
                    'tax_id':False,
                    'promotion_price':price_unit,
                    'is_promotion': True,
                    'promotion_product':True,
                    }
                    if self.order_line:
                        values['sequence'] = self.order_line[-1].sequence + 1
                    sale_order_line = SaleOrderLine.sudo().create(values)
        elif promotion.bogo_sale_on in ['bogelse']:
            sol=SaleOrderLine.search([('order_id','=',self.id),('promotion_product','=',True)])
            for line in sol:
                qty=line.product_uom_qty
                free_qty=qty/promotion.bogoelse_Aproduct_unit
                price_unit=price_unit*int(free_qty)
                line.write({'promotion_product':False,'promotion_price':0.0})
                name = promotion.free_product.name_get()[0][1]
                if promotion.free_product.description_sale:
                    name += '\n' + promotion.free_product.description_sale
                if line:
                    values = {
                    'order_id': self.id,
                    'name': name,
                    'product_uom_qty': int(free_qty)*promotion.bogoelse_Bproduct_unit,
                    'product_uom': promotion.free_product.uom_id.id,
                    'product_id':promotion.free_product.id,
                    'price_unit': promotion.free_product.lst_price,
                    'tax_id':False,
                    'promotion_price':price_unit,
                    'is_promotion': True,
                    'promotion_product':True,
                    }
                    if self.order_line:
                        values['sequence'] = self.order_line[-1].sequence + 1
                    sale_order_line = SaleOrderLine.sudo().create(values)
        else:
            sol=SaleOrderLine.search([('order_id','=',self.id),('promotion_product','=',True)])
            for line in sol:
                line.write({'promotion_product':False,'promotion_price':price_unit})
        name = promotion.promotion_product_id.name_get()[0][1]
        if promotion.promotion_product_id.description_sale:
            name += '\n' + promotion.free_product.description_sale
        values = {
                'order_id': self.id,
                'name': promotion.name,
                'product_uom_qty': 1,
                'product_uom': promotion.promotion_product_id.uom_id.id,
                'product_id':promotion.promotion_product_id.id,
                'price_unit': price_unit,
                'tax_id':False,
                'is_promotion': True,
            }
        if self.order_line:
            values['sequence'] = self.order_line[-1].sequence + 1
        sol = SaleOrderLine.sudo().create(values)
        return sol
    
class SaleorderLine(models.Model):
    _inherit = 'sale.order.line'

    is_promotion = fields.Boolean(string="Is a Promotion", default=False)
    promotion_price = fields.Float(string="Promotion Amount",default=0.0)
    promotion_product = fields.Boolean(string="Is a Free Promotion Product",default=False)
   
    @api.depends('product_id','product_uom_qty')
    def onchange_promotion_order_line(self):
        promoline=self.env['sale.order.line'].search([('order_id','=',self.order_id.id),('is_promotion','=',True)]).write({'price_unit':0.0,'product_uom_qty':0.0})
        print "onchang saleorderline"
        self.order_id.write({'promotion_id':False})
        return {}
    
    '''@api.multi
    def unlink(self):
        for line in self:
            if line.order_id.promotion_id:
                raise UserError(_('You can not remove a sale order line. When Promotion is set'))
        return super(SaleorderLine,self).unlink()'''
    
    
class SaleReport(models.Model):
    _inherit = 'sale.report'
    
    coupon_code = fields.Char("Coupon code")
    promotion_product = fields.Boolean(string="Promotion Product",default=False)
    
    def _select(self):
        select_str = """
            WITH currency_rate as (%s)
             SELECT min(l.id) as id,
                    l.product_id as product_id,
                    l.promotion_product as promotion_product,
                    t.uom_id as product_uom,
                    sum(l.product_uom_qty / u.factor * u2.factor) as product_uom_qty,
                    sum(l.qty_delivered / u.factor * u2.factor) as qty_delivered,
                    sum(l.qty_invoiced / u.factor * u2.factor) as qty_invoiced,
                    sum(l.qty_to_invoice / u.factor * u2.factor) as qty_to_invoice,
                    sum(l.price_total / COALESCE(cr.rate, 1.0)) as price_total,
                    sum(l.price_subtotal / COALESCE(cr.rate, 1.0)) as price_subtotal,
                    count(*) as nbr,
                    s.name as name,
                    s.date_order as date,
                    s.state as state,
                    s.coupon_code as coupon_code,
                    s.partner_id as partner_id,
                    s.user_id as user_id,
                    s.company_id as company_id,
                    extract(epoch from avg(date_trunc('day',s.date_order)-date_trunc('day',s.create_date)))/(24*60*60)::decimal(16,2) as delay,
                    t.categ_id as categ_id,
                    s.pricelist_id as pricelist_id,
                    s.project_id as analytic_account_id,
                    s.team_id as team_id,
                    p.product_tmpl_id,
                    partner.country_id as country_id,
                    partner.commercial_partner_id as commercial_partner_id,
                    sum(p.weight * l.product_uom_qty / u.factor * u2.factor) as weight,
                    sum(p.volume * l.product_uom_qty / u.factor * u2.factor) as volume
        """ % self.env['res.currency']._select_companies_rates()
        return select_str


    def _group_by(self):
        group_by_str = """
            GROUP BY l.product_id,
                    l.order_id,
                    l.promotion_product,
                    t.uom_id,
                    t.categ_id,
                    s.name,
                    s.date_order,
                    s.partner_id,
                    s.user_id,
                    s.state,
                    s.company_id,
                    s.pricelist_id,
                    s.project_id,
                    s.coupon_code,
                    s.team_id,
                    p.product_tmpl_id,
                    partner.country_id,
                    partner.commercial_partner_id
        """
        return group_by_str    
    