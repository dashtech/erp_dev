import odoo
import string
import random
import pytz
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta,datetime
from .. import barcode
from ..barcode.writer import ImageWriter
import base64
import time
import hashlib


class Promotion(models.Model):
    _name='promotion.method'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.multi
    def _get_promo_product(self):
        product_id = self.env['ir.values'].sudo().get_default('sale.config.settings', 'promotion_product_id')
        return self.env['product.product'].search([('id','=',product_id)])
    
    @api.multi
    def _get_promo_product_category(self):
        category_id = self.env['ir.values'].sudo().get_default('sale.config.settings', 'promotion_product_category_id')
        return self.env['product.category'].search([('id','=',category_id)])
    
    @api.model
    def _tz_get(self):
        # put POSIX 'Etc/*' entries at the end to avoid confusing users - see bug 1086728
        return [(tz, tz) for tz in sorted(pytz.all_timezones, key=lambda tz: tz if not tz.startswith('Etc/') else '_')]

    _sql_constraints = [
        ('coupon_code', 'unique(coupon_code)', 'Cant be duplicate value for promotion code field!')]
    
    name=fields.Char("Promotion Name",required=True)
    sequence_name = fields.Char(readonly=True, default=lambda self: ('New'), required=True)
    applied_on = fields.Selection([
        ('global', 'Global Level'),
        ('product_category', ' Category Level'),
        ('product', 'Product Level'),
        ('product_variant', 'Variant Level')], "Apply On",
        default='global', required=True,track_visibility='onchange',
        help='PromotionList Item applicable on selected option')
    
    promotion_product_id = fields.Many2one(
        'product.product', 'Promotion Product',default=_get_promo_product, domain="[('is_promo_product', '=', True)]",context="{'default_is_promo_product':1,'default_type':'service'}",
        help="Specify a product for set product in sale order.")
    product_ids = fields.Many2many(
        'product.product', string='Product', ondelete='cascade',domain="[('type','!=','service')]",
        help="Specify a products in which the Promotion is apply.")
    product_tmpl_ids = fields.Many2many(
        'product.template',string= 'Product Template', ondelete='cascade',domain="[('type','!=','service')]",
        help="Specify a template in which the Promotion is apply.")
    categ_ids = fields.Many2many(
        'product.category', string='Product Category', ondelete='cascade',
        help="Specify a product category if this promotion only applies to products belonging to these categories.")
    coupon_code = fields.Char(string="Code",help="Coupon code to apply promotion in sale order")
    base_promotionlist_id = fields.Many2one('promotion.method', 'Other Pricelist')
    min_order_amount = fields.Float('Min. Order Amount',help="Specify the minimum amount from where sales become eligible for the discount coupon")
    min_order_quantity = fields.Float('Min. Order Quantity', default=1.0,help="Specify the minimum Quantity required to activate discount coupon")
    date_start = fields.Date('Promotion Date Period', help="Select promotion period",required=True)
    date_end = fields.Date('End Date', help="Ending date of promotion code",required=True)
    is_specific_time=fields.Boolean("Apply Specific Time Period",default=False)
    time_start = fields.Float('Promotion Time Period')
    time_end = fields.Float('End Time')
    timezone = fields.Selection(_tz_get, string='Timezone', default=lambda self: self._context.get('timezone'))
    compute_price = fields.Selection([
        ('fixed', 'Fixed Price Discount'),
        ('percentage', 'Percentage Discount'),
        ('range', 'Range based Discount'),
        ('other_promotionlist','Clubbed Promotion'),
        ('bogo_sale','BOGO Offer')], index=True,track_visibility='onchange', default='fixed')
    fixed_price = fields.Float('Fixed Price')
    percent_price = fields.Float('Percentage Price')
    price_discount = fields.Float('Price Discount', default=0,help='Specify the extra percentage to calculated with the other promotion amount.')
    price_surcharge = fields.Float(
        'Price Surcharge',help='Specify the fixed amount to add to the amount calculated with the discount.')
    range_based_on = fields.Selection([
        ('price','Price'),
        ('qty','Quantity')], index=True, default='price')
    rule_based_ids = fields.One2many('promotion.method.rule.based','promo_id',string='Rule Lines')
    customer_ids = fields.Many2many('res.partner',string="Customers",help="Specify if Promotion apply for specific customers")
    promo_name = fields.Char(compute="_get_promo_name",string="Promotion name")
    active = fields.Boolean(string="Active",default=True)
    max_limit_per_user = fields.Integer("Limit",default=1,help="Specify for the limit to use coupon code per user")
    max_promotion_amount=fields.Float("Max Promotion Amount",help="Specify the maximum discount should be allowed per sales")
    order_count = fields.Integer(
        '# Orders', compute='_compute_order_count',
        help="The number of orders in which this promotion is applied")
    orderline_count = fields.Integer(
        '# OrdeLines', compute='_compute_orderline_count',
        help="The number of orderlines in which this promotion is applied")
    quotation_count=fields.Integer(
        '# Quotations', compute='_compute_quotation_count',
        help="The number of quotation in which this promotion is applied")
    quotationline_count=fields.Integer(
        '# QuotationLines', compute='_compute_quotationline_count',
        help="The number of quotationlines in which this promotion is applied")
    total_salepromo_amount=fields.Float(compute='_compute_orderpromo_amount',readonly=True,string="Promotion Given")
    state=fields.Selection([('draft','Draft'),('approve','Approved'),('close','Closed'),('cancel','Cancelled'),],default='draft')
    is_for_specific_customers=fields.Boolean("Apply only for Specific Customers?",default=False)
    is_for_specific_area=fields.Boolean("Apply only for Specific Area?",default=False)
    country_ids = fields.Many2many('res.country','promotion_country_rel', 'promotion_id', 'country_id', 'Countries')
    state_ids = fields.Many2many('res.country.state','promotion_state_rel', 'promotion_id', 'state_id', 'States')
    zip_from = fields.Char('Zip From')
    zip_to = fields.Char('Zip To')
    partner_category_ids=fields.Many2many('res.partner.category',string="Customer Groups")
    bogo_sale_on=fields.Selection([
        ('bxgy','Buy (X Unit) of Product , Get (X Unit) of Product Free'),
        ('bogelse','Buy (X Unit) of Product Get (Y Unit) of Another Product Free'),
        ('promo_on_prdct_B','Buy (X Unit) of Product A, Get (Y Unit) of Product B for $ or % Discount')], index=True, default='bxgy')
    free_product=fields.Many2one('product.product',string="Discounted Product",domain="[('type','!=','service')]")
    promo_on_prdct_B_on=fields.Selection([
        ('fixed_price','Fixed Discount'),
        ('percentage','Percentage Discount')],string="Based On",index=True)
    bxgy_Aproduct_unit=fields.Integer("Min Product Qty",default=1)
    bxgy_Bproduct_unit=fields.Integer("Discounted Product Qty",default=1)
    bogoelse_Aproduct_unit=fields.Integer("Min Product Qty",default=1)
    bogoelse_Bproduct_unit=fields.Integer("Discounted Product Qty",default=1)
    Aproduct_unit=fields.Integer("Product Qty", default=1)
    Bproduct=fields.Many2one('product.product',string="Discounted Product",domain="[('type','!=','service')]")
    Bproduct_unit=fields.Integer("Discounted Product Qty", default=1)
    promo_on_prdct_B_fixed_price=fields.Float("Fixed Discount")
    promo_on_prdct_B_percentage_price=fields.Float("Percentage Discount")
    promotion_budget=fields.Float("Promotion Budget")
    max_coupon_limit = fields.Integer("Total Usage Limit",default=1)
    bar_code_sequence = fields.Char(string="Barcode random No",help="random digit 12 for generate barcode", default=lambda self: ('New'), required=True)
    bar_code_ean13 = fields.Char(string="Barcode",help="Bar code to apply promotion in sale order")
    bar_image= fields.Binary(compute="generate_barcode",string="Barcode Image", store=True) 
    barcode_discription = fields.Text("Discription")
    used_promo_count=fields.Integer(compute="_get_used_promo")
    

    def _get_used_promo(self):
        for promo in self:
            saleorder=self.env['sale.order'].search_count([('state','in',('sale','done')),('promotion_id','=',promo.id)])
            promo.used_promo_count=saleorder
    
    @api.onchange('is_for_specific_area')
    def onchange_area_boolean(self):
        for promo in self:
            if promo.is_for_specific_area==False:
                promo.country_ids=False
                promo.state_ids=False
                promo.zip_from=''
                promo.zip_to=''
                
    @api.onchange('is_for_specific_customers')
    def onchange_customer_boolean(self):
        for promo in self:
            if promo.is_for_specific_customers==False:
                promo.customer_ids=False
                promo.partner_category_ids=False
                
    @api.onchange('is_specific_time')
    def onchange_time_boolean(self):
        for promo in self:
            if promo.is_specific_time==False:
                promo.time_start=0.0
                promo.time_end=0.0
    
    @api.onchange('state_ids')
    def onchange_states(self):
        self.country_ids = [(6, 0, self.country_ids.ids + self.state_ids.mapped('country_id.id'))]

    @api.onchange('country_ids')
    def onchange_countries(self):
        self.state_ids = [(6, 0, self.state_ids.filtered(lambda state: state.id in self.country_ids.mapped('state_ids').ids).ids)]

    @api.one
    @api.depends('bar_code_ean13')
    def generate_barcode(self):  
        if self.bar_code_ean13:
            bar_code=self.bar_code_ean13
            EAN = barcode.get_barcode_class('ean13')
            ean = EAN(bar_code, writer=ImageWriter())
            ts = time.time()
            time_stamp = datetime.fromtimestamp(ts).strftime('%Y%m%d%H%M%S')
            tmp_file_name ='/tmp/%(filename)s'%({'filename': hashlib.sha1(time_stamp).hexdigest()[0:7]})
            fullname=ean.save(tmp_file_name)
            file_obj = open(fullname)
            self.bar_image =base64.encodestring(file_obj.read())
            
            
    @api.multi
    def action_coupon_send(self):
        '''
        This method opens a window to compose an email.
        '''
       
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
                template_id = self.env.ref('promotion_ept.email_template_edi_promotion')
        except ValueError:
                template_id = False
        try:
                compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
                compose_form_id = False
        ctx = dict()
            
        ctx.update({
                'default_model': 'promotion.method',
                'default_res_id': self.ids[0],
                'default_use_template': bool(template_id.id),
                'default_template_id': template_id.id,
                'default_composition_mode': 'comment',
                'mark_so_as_sent': True,
   
               
        })
        return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'mail.compose.message',
                'views': [(compose_form_id, 'form')],
                'view_id': compose_form_id,
                'target': 'new',
                'context': ctx,
            }

    
    @api.constrains('promotion_product_id','coupon_code','time_start','time_end','date_start','date_end','promotion_product_id','max_coupon_limit','max_limit_per_user','applied_on','percent_price','price_discount','price_surcharge','fixed_price','compute_price','rule_based_ids','min_order_amount','min_order_quantity','base_promotionlist_id','product_ids','product_tmpl_ids','categ_ids','bxgy_Aproduct_unit','bogoelse_Aproduct_unit','Aproduct_unit','Bproduct_unit','customer_ids','country_ids','state_ids','partner_category_ids')
    def _check_something(self):
        '''
            This method use for validation at promotion create time.
        '''
        now = fields.datetime.now()
        current = now - timedelta(minutes = 5)
       
        for record in self:
            date_start=datetime.strptime(record.date_start, '%Y-%m-%d')
            date_end=datetime.strptime(record.date_end,'%Y-%m-%d')
            if record.promotion_product_id.id==False:
                raise ValidationError(_("Please Set Promotion Product From Promotion Configuration To Create Promotion."))
            code=record.coupon_code
            if len(code)<7 or len(code)>10:
                raise ValidationError(_("Coupon code length should be in 7 to 10 Character."))
            if record.promotion_product_id.categ_id!=self._get_promo_product_category():
                raise ValidationError(_("Promotion Product's category should be in sale config setting promotion product category selected"))
            if record.percent_price > 99:
                raise ValidationError(_("It has to be less then 100"))
            if record.price_discount > 99:
                raise ValidationError(_("It has to be less then 100"))
            if record.compute_price in ['fixed']:
                if record.fixed_price<=0.00:
                    raise ValidationError(_("Please Enter some Value for Calculation of promotion amount"))
            if record.compute_price in ['percentage']:
                if record.percent_price<=0.00:
                    raise ValidationError(_("Please Enter  some Value for Calculation of promotion amount"))
            if record.compute_price in ['range']:
                if record.rule_based_ids:
                    for id in record.rule_based_ids:
                        if id==False:
                            raise ValidationError(_("Please Enter Range"))
                else:
                    raise ValidationError(_("Please Enter Range"))
            if not record._context.get('key'):
                if record.date_start!=False and date_start.date()<current.date():
                    raise ValidationError(_("Please Enter valid Start date"))
            if record.date_end!=False and date_end<date_start:
                raise ValidationError(_("Please Enter valid End date"))
            if record.date_end!=False and record.date_start==False:
                raise ValidationError(_("Please Enter Start date"))
            if record.time_start!=False and record.time_start>25 or record.time_start<0.0:
                raise ValidationError(_("Please Enter Valid Start Time"))
            if record.time_end!=False and record.time_end>25 or record.time_end<0.0:
                raise ValidationError(_("Please Enter Valid End Time"))
            if record.time_end!=False and record.time_start==False:
                raise ValidationError(_("Please Enter Start time"))
            if record.time_start!=False and record.time_end==False:
                raise ValidationError(_("Please Enter End tme"))
            if record.max_coupon_limit<-1 or record.max_coupon_limit==0 or record.max_limit_per_user<-1 or record.max_limit_per_user==0 or record.max_limit_per_user>record.max_coupon_limit:
                raise ValidationError(_("Please Enter Valid Limit for Coupon."))
            if record.max_promotion_amount!=0.0 and record.fixed_price>record.max_promotion_amount:
                raise ValidationError(_("Please Varify Maximum Promotion Amount and Fixed Amount"))
            if record.customer_ids and (record.country_ids or record.state_ids):
                for customer in record.customer_ids:
                    if record.country_ids and customer.country_id and customer.country_id not in record.country_ids:
                        raise ValidationError(_("Please Varify Customer Address and Countries you set in Promotion."))
                    if record.state_ids and customer.state_id and customer.state_id not in record.state_ids:
                        raise ValidationError(_("Please Varify Customer Address and States you set in Promotion."))
            if record.partner_category_ids and (record.country_ids or record.state_ids):
                for group in record.partner_category_ids:
                    for customer in group.partner_ids:
                        if record.country_ids and customer.country_id and customer.country_id not in record.country_ids:
                            raise ValidationError(_("Please Varify Customer Group Address and Countries you set in Promotion."))
                        if record.state_ids and customer.state_id and customer.state_id not in record.state_ids:
                            raise ValidationError(_("Please Varify Customer Group Address and States you set in Promotion."))
            if record.range_based_on==False:
                raise ValidationError(_("Please Select any Range Based On."))
            '''if record.range_based_on=='qty':
                for rule in record.rule_based_ids:
                    if rule.to_end<record.min_order_quantity:
                       raise ValidationError("Please Varify Minimum Order Quantity and Range Quantity")
            if record.range_based_on=='price':
                for rule in record.rule_based_ids:
                    if rule.to_end<record.min_order_amount:
                       raise ValidationError("Please Varify Minimum Order Amount and Range Amount")
            if record.bogo_sale_on=='bxgy':
                if record.min_order_quantity<record.bxgy_Aproduct_unit:
                    raise ValidationError("Please Varify Minimum Order Quantity and BOGO Minimum Quantity")
            if record.bogo_sale_on=='bogelse':
                if record.min_order_quantity<record.bogoelse_Aproduct_unit:
                    raise ValidationError("Please Varify Minimum Order Quantity and BOGO Minimum Quantity")
            if record.bogo_sale_on=='promo_on_prdct_B':
                if record.min_order_quantity<record.Aproduct_unit or record.min_order_quantity<record.Bproduct_unit:
                    raise ValidationError("Please Varify Minimum Order Quantity and BOGO Minimum Quantity") '''          
            if record.base_promotionlist_id:
                if record.price_discount==0.0 and record.price_surcharge==0.0:
                    raise ValidationError(_("Please Add Extra Percentage or Extra off."))
                base_date=datetime.strptime(record.base_promotionlist_id.date_end, '%Y-%m-%d %H:%M:%S').date()
                date=datetime.strptime(record.date_end, '%Y-%m-%d %H:%M:%S').date()
                if base_date<date:
                    raise ValidationError(_("Please Varify Both Promotion End Dates."))
                applied=record.applied_on
                if applied=='product_category':
                    if record.base_promotionlist_id.applied_on=='product_category':
                        categ=self.env['promotion.method'].search([('id','=',record.id),('categ_ids','in',record.base_promotionlist_id.categ_ids.ids)])
                        if not categ:
                            raise ValidationError(_("Please Varify Clubbed Promotion Category"))
                if applied=='product': 
                    if record.base_promotionlist_id.applied_on=='product':
                        template=self.env['promotion.method'].search([('id','=',record.id),('product_tmpl_ids','in',record.base_promotionlist_id.product_tmpl_ids.ids)])
                        if not template:
                            raise ValidationError(_("Please Varify Clubbed Promotion Product"))
                if applied=='product_variant':
                    if record.base_promotionlist_id.applied_on=='product_variant':
                        products=self.env['promotion.method'].search([('id','=',record.id),('product_ids','in',record.base_promotionlist_id.product_ids.ids)])
                        if not products:
                            raise ValidationError(_("Please Varify Clubbed Promotion Product variant"))
                       
    @api.one
    def draft(self):
         self.write({'state': 'draft'})
    
    @api.one
    def approve(self):
         self.write({'state': 'approve'})
         
    @api.one
    def close(self):
         self.write({'state': 'close'})
         
    @api.one
    def cancel(self):
         self.write({'state': 'cancel'})
               
    def _compute_orderpromo_amount(self):
        '''
            This method use for compute total promotion amount given by specific promotion.
        '''
        for promo in self:
            if promo.base_promotionlist_id:
                orders=self.env['sale.order'].search([('promotion_id', '=', promo.id),('promotion_id','!=',promo.base_promotionlist_id.id),('state','in',('sale','done'))])
                amount=0.0
                for order in orders:
                    amount+=order.promo_price
                promo.total_salepromo_amount=-(amount)
            else:
                orders=self.env['sale.order'].search([('promotion_id', '=', promo.id),('state','in',('sale','done'))])
                amount=0.0
                for order in orders:
                    amount+=order.promo_price
                promo.total_salepromo_amount=-(amount)
    
    def _compute_order_count(self):
        '''
            This method use for calculate total order in which particular promotion applied.
        '''
        for promo_id in self:
            if promo_id.base_promotionlist_id:
                orders=self.env['sale.order'].search_count([('promotion_id', '=', promo_id.id),('promotion_id','!=',promo_id.base_promotionlist_id.id),('state','in',('sale','done'))])
                promo_id.order_count=orders
            else:
                orders=self.env['sale.order'].search_count([('promotion_id', '=', promo_id.id),('state','in',('sale','done'))])
                promo_id.order_count=orders
        
    def _compute_orderline_count(self):
        '''
            This method use for calculate total orderline in which particular promotion applied.
        '''
        for promo_id in self:
            if promo_id.base_promotionlist_id:
                orderlines=self.env['sale.order.line'].search_count([('promotion_price','<',0.0),('order_id.promotion_id','=',promo_id.id),('order_id.promotion_id','!=',promo_id.base_promotionlist_id.id),('order_id.state','in',('sale','done'))])
                promo_id.orderline_count=orderlines
            else:
                orderlines=self.env['sale.order.line'].search_count([('promotion_price','<',0.0),('order_id.promotion_id','=',promo_id.id),('order_id.state','in',('sale','done'))])
                promo_id.orderline_count=orderlines
            
    def _compute_quotation_count(self):
        '''
            This method use for calculate total quotation in which particular promotion applied.
        '''
        for promo_id in self:
            if promo_id.base_promotionlist_id:
                orders=self.env['sale.order'].search_count([('promotion_id', '=', promo_id.id),('promotion_id','!=',promo_id.base_promotionlist_id.id),('state','not in',('sale','done','cancel'))])
                promo_id.quotation_count=orders
            else:
                orders=self.env['sale.order'].search_count([('promotion_id', '=', promo_id.id),('state','not in',('sale','done','cancel'))])
                promo_id.quotation_count=orders
        
    def _compute_quotationline_count(self):
        '''
            This method use for calculate total quotationline in which particular promotion applied.
        '''
        for promo_id in self:
            if promo_id.base_promotionlist_id:
                orderlines=self.env['sale.order.line'].search_count([('promotion_price','<',0.0),('order_id.promotion_id','=',promo_id.id),('order_id.promotion_id','!=',promo_id.base_promotionlist_id.id),('order_id.state','not in',('sale','done','cancel'))])
                promo_id.quotationline_count=orderlines
            else:
                orderlines=self.env['sale.order.line'].search_count([('promotion_price','<',0.0),('order_id.promotion_id','=',promo_id.id),('order_id.state','not in',('sale','done','cancel'))])
                promo_id.quotationline_count=orderlines
            
            
    @api.onchange('applied_on', 'compute_price')
    def bogo_change(self):
        '''
            This method use for pop-up message while its applied on Globally and set BOGO offere.
        '''
        if self.applied_on=='global' and self.compute_price=='bogo_sale':
            return {'warning':{'title':_('Warning'),'message':_('You are Set BOGO and its applied On Global')}}
    
    @api.onchange('range_based_on')
    def _onchange_rule_basedon(self):
        '''
            This method use for delete rules while user change rule based on price to quantity or visa versa. 
        '''
        for line in self.rule_based_ids:
            line.write({'promo_id':False})
    
    def get_code(self):
        '''
            This method use for generate coupon code. 
        '''
        size = 7
        chars = string.ascii_uppercase + string.digits 
        return ''.join(random.choice(chars) for _ in range(size))

    @api.model   
    def create(self, vals):
        if vals['coupon_code']==False: 
            vals['coupon_code']=self.get_code()  
        if vals['coupon_code']:
            code=vals['coupon_code']
            vals['coupon_code']=code.upper()
        if vals.get('sequence_name', 'New') == 'New':
            vals['sequence_name'] = self.env['ir.sequence'].next_by_code('promotion.method') or 'New'
        if vals.get('bar_code_sequence', 'New') == 'New':
            vals['bar_code_sequence'] = self.env['ir.sequence'].get('barcode.promotion.method') or 'New'
        EAN = barcode.get_barcode_class('ean13')
        vals['bar_code_ean13']=EAN(vals['bar_code_sequence'], writer=ImageWriter())
        res_id = super(Promotion,self).create(vals) 
        return res_id
       
    @api.depends("name", "sequence_name")
    def _get_promo_name(self):
        '''
            This method use for set name in tree view like sequence+promoname.
        '''
        for s in self:
            name = s.name or ''
            sequence_name = s.sequence_name or ''
            name = "["+str(sequence_name) + "] " + str(name) 
            s.promo_name = name 
    
    @api.multi
    def unlink(self):
        
        for promotion in self:
            sale_order=self.env['sale.order'].search([('promotion_id','=',promotion.id),('state','not in',('draft', 'cancel'))])
            if sale_order:
                raise UserError(_('You can not delete a Promotion which is set in sale order! Try to cancel sale order before.'))
        return super(Promotion, self).unlink()        
    
    @api.multi
    def set_promotion(self,order,promotion,other_promotion):
        '''
            This method use for apply promotion.
        '''
        price_unit=0.0
        cnt=0
        if promotion.state in ['approve']:
            qty=0
            line_count=0
            for l in order.order_line:
                line_count+=1
                qty+=l.product_uom_qty
            amount=order.amount_untaxed
            min_order_amount=0.0
            min_order_quantity=0.0
            if promotion.min_order_amount>0.0:
                min_order_amount=promotion.min_order_amount
            if promotion.min_order_quantity>0.0:
                min_order_quantity=promotion.min_order_quantity
            for line in order.order_line:                
                if qty>=min_order_quantity and amount>=min_order_amount and line.price_unit>0.0:
                    if promotion.applied_on in ['global']:
                        if line.promotion_price!=0.0 and promotion.bogo_sale_on=='promo_on_prdct_B':
                            #this is for when apply in gobal and promotion is not apply on free product
                            line.write({'promotion_product':False})
                            price_unit=0.0
                        else:    
                            price=self._compute_price(order,promotion,line)
                            cnt+=1
                        if promotion.bogo_sale_on not in['promo_on_prdct_B']:
                            if other_promotion==False: 
                                line.write({'promotion_price':price})
                        if promotion.compute_price in ['percentage','bogo_sale','range']:
                            price_unit=price_unit+price 
                        else:
                            price_unit=price
                    elif promotion.applied_on in ['product']:
                        for product_tmpl in promotion.product_tmpl_ids:
                            if line.product_id.product_tmpl_id.id==product_tmpl.id:
                                price=self._compute_price(order,promotion,line)
                                cnt+=1
                                if promotion.bogo_sale_on not in['promo_on_prdct_B']:
                                    if other_promotion==False: 
                                        line.write({'promotion_price':price})
                                price_unit=price_unit+price
                                
                    elif promotion.applied_on in ['product_variant']:
                        for product in promotion.product_ids:
                            if line.product_id.id==product.id:
                                price=self._compute_price(order,promotion,line)
                                cnt+=1
                                if promotion.bogo_sale_on not in['promo_on_prdct_B']:
                                    if other_promotion==False: 
                                        line.write({'promotion_price':price})
                                price_unit=price_unit+price
                                
                    elif promotion.applied_on in ['product_category']:
                        for category in promotion.categ_ids:
                            if line.product_id.categ_id.id == category.id:
                                price=self._compute_price(order,promotion,line)
                                cnt+=1
                                if promotion.bogo_sale_on not in['promo_on_prdct_B']:
                                    if other_promotion==False: 
                                        line.write({'promotion_price':price})
                                price_unit=price_unit+price
                else:
                    if other_promotion==False:
                        order.message_post(body=("<b>Sales is Not Qualifying Coupon Code Discount Criteria.</b>"))
                        return price_unit   
            if cnt==0:
                order.message_post(body=("<b>Order not Contain Promotion Criteria product.</b>"))         
            if promotion.applied_on in ['global'] and promotion.compute_price in ['fixed']:
                self.update_price(price_unit,order)
            price_unit=self.extra_validation(order,price_unit)
            if price_unit<0.0:
                if promotion.compute_price in ['other_promotionlist'] and promotion.applied_on in ['global']:
                    unit_price=price_unit/line_count
                    for line in order.order_line:
                        line.write({'promotion_price':unit_price})
                if promotion.compute_price not in ['bogo_sale']:
                    for ol in order.order_line:
                        if ol.promotion_price!=0.0:
                            if ol.price_unit*ol.product_uom_qty<-(ol.promotion_price):
                                self.update_price(price_unit, order)
            else:
                return price_unit
        else:
            price_unit=0.0
            order.message_post(body=("<b>Promotion not in Approve State</b>"))
            return price_unit
        return price_unit
    
    def update_price(self,promo_price,order):
        '''
            This method use when promotion amount is gretar then product unit price.
        '''
        ratio=promo_price/order.amount_untaxed
        for line in order.order_line:
            price=line.product_uom_qty*line.price_unit
            apply_price=price*ratio
            line.write({'promotion_price':apply_price})    
        
    def extra_validation(self,order,price_unit):
        '''
            This method use for check extra validation like date,time,customer,area,etc.. 
        '''
        so_count=self.env['sale.order'].search_count([('partner_id','=',order.partner_id.id),('promotion_id','=',order.promotion_id.id),('state','in',('sale','done'))])
        s_cnt=self.env['sale.order'].search_count([('state','in',('sale','done')),('promotion_id','=',order.promotion_id.id)])
        if s_cnt<order.promotion_id.max_coupon_limit or order.promotion_id.max_coupon_limit==-1:
            if so_count<order.promotion_id.max_limit_per_user or order.promotion_id.max_limit_per_user==-1:
                    confirm_date=datetime.now().date()
                    start_date=datetime.strptime(order.promotion_id.date_start, '%Y-%m-%d')
                    end_date=datetime.strptime(order.promotion_id.date_end, '%Y-%m-%d')
                    cntr=0
                    if order.promotion_id.customer_ids:
                        if order.partner_id in order.promotion_id.customer_ids:
                                promotion = self.verify_address(order.partner_invoice_id)
                                if promotion:
                                    if confirm_date>=start_date.date() and confirm_date<=end_date.date():
                                        if order.promotion_id.is_specific_time:
                                            promotion=self.check_time(order)
                                            if promotion:
                                                cntr=cntr+1
                                                return price_unit
                                            else:
                                                price_unit=0.0
                                                order.message_post(body=("<b>You are requested to check Time Limit for Today.</b>"))
                                                return price_unit
                                        else:
                                            cntr=cntr+1
                                            return price_unit
                                    else:
                                        price_unit=0.0
                                        order.message_post(body=("<b>You are requested to check the date criteria.</b>"))
                                        return price_unit
                                else:
                                    price_unit=0.0
                                    order.message_post(body=("<b>Sorry,You are not applicable for this Coupon.</b>"))
                                    return price_unit
                    elif order.promotion_id.partner_category_ids:
                        if order.promotion_id.partner_category_ids in order.partner_id.category_id:
                                promotion = self.verify_address(order.partner_invoice_id)
                                if promotion:
                                    if confirm_date>=start_date.date() and confirm_date<=end_date.date():
                                        if order.promotion_id.is_specific_time:
                                            promotion=self.check_time(order)
                                            if promotion:
                                                cntr=cntr+1
                                                return price_unit
                                            else:
                                                price_unit=0.0
                                                order.message_post(body=("<b>You are requested to check Time Limit for Today.</b>"))
                                                return price_unit
                                        else:
                                            cntr=cntr+1
                                            return price_unit
                                    else:
                                        price_unit=0.0
                                        order.message_post(body=("<b>Oops, You are little bit late Coupon is expired.</b>"))
                                        return price_unit
                                else:
                                    price_unit=0.0
                                    order.message_post(body=("<b>Sorry,You are not applicable for this Coupon.</b>"))
                                    return price_unit
                     
                    else:
                        promotion = self.verify_address(order.partner_invoice_id)
                        if promotion:
                            if confirm_date>=start_date.date() and confirm_date<=end_date.date():
                                if order.promotion_id.is_specific_time:
                                    promotion=self.check_time(order)
                                    if promotion:
                                        return price_unit
                                    else:
                                        price_unit=0.0
                                        order.message_post(body=("<b>You are requested to check Time Limit for Today.</b>"))
                                        return price_unit
                                else:
                                    return price_unit
                            else:
                                price_unit=0.0
                                order.message_post(body=("<b>You are requested to check the date criteria.</b>"))
                                return price_unit
                        else:
                            price_unit=0.0
                            order.message_post(body=("<b>Sorry,You are not applicable for this Coupon.</b>"))
                            return price_unit 
                            
                    if cntr==0:
                        price_unit=0.0
                        order.message_post(body=("<b>Sorry,You are not applicable for this Coupon.</b>"))
                        return price_unit                               
                                
            else:
                price_unit=0.0
                order.message_post(body=("<b>Oops, Limit of Coupon Code use per user goen to maximum.</b>"))
                return price_unit  
        else:
            price_unit=0.0
            order.message_post(body=("<b>Oops, Limit of Coupon Code usage goen to maximum.</b>"))
            return price_unit
    
    def check_time(self,order):
        '''
            This method use for checking perticular timezone timming.
        '''
        confirm_time=datetime.utcnow()
        time_zone=order.promotion_id.timezone
        time_zone = pytz.timezone(time_zone)
        cnfm_date=confirm_time.now(time_zone)
        str_date=cnfm_date.strftime('%H:%M')
        time_split = [int(n) for n in str_date.split(":")]
        current_utc_time_float = time_split[0] + time_split[1]/60.0
        if current_utc_time_float>=order.promotion_id.time_start and current_utc_time_float<=order.promotion_id.time_end:
            return self
        else:
            return False
    
    @api.multi
    def verify_address(self, contact):
        '''
            This method use for checking area.
        '''
        self.ensure_one()
        if self.country_ids and contact.country_id not in self.country_ids:
            return False
        if self.state_ids and contact.state_id not in self.state_ids:
            return False
        if self.zip_from and (contact.zip or '') < self.zip_from:
            return False
        if self.zip_to and (contact.zip or '') > self.zip_to:
            return False
        return self
       
    def _compute_price(self,order,promotion,line): 
        '''
            This method use for calculate promotion amount. 
        '''
        currency_id=order.partner_id.currency_id     
        currency_factor=currency_id._get_conversion_rate(currency_id,order.pricelist_id.currency_id)
        price=0.0
        if promotion.compute_price in ['fixed']:
            price_unit =-promotion.fixed_price*currency_factor         
                             
        elif promotion.compute_price in ['percentage']:
            price=line.price_unit*line.product_uom_qty
            price_unit =-(price*(promotion.percent_price))/100
            
        elif promotion.compute_price in ['other_promotionlist']:
                price=0.0
                price=self.set_promotion(order, promotion.base_promotionlist_id,other_promotion=True)
                if price==0.0:
                    price_temp=-line.price_unit*line.product_uom_qty
                    price_unit=((price_temp*(promotion.price_discount))/100 - promotion.price_surcharge)
                else:
                    if promotion.applied_on in ['product','product_category','product_variant']:
                        price_temp=line.price_unit*line.product_uom_qty+price
                    else:
                        price_temp=order.amount_untaxed+price
                    price_unit=-((price_temp*(promotion.price_discount))/100 + promotion.price_surcharge)
                                
                
        elif promotion.compute_price in ['range']:
            price_unit=0.0
            if promotion.range_based_on in ['price']:
                for rule in promotion.rule_based_ids:
                    if rule.price_based_on in ['fixed']:
                        if rule.to_end == -1:
                            if line.price_unit*line.product_uom_qty>=rule.from_start:
                                price_unit=-rule.based_on_fixed_price*currency_factor
                            else:
                                order.message_post(body=("<b>Order Amount is not Statisfied Promotion Criteria."))
                        else:
                            if line.price_unit*line.product_uom_qty>=rule.from_start and line.price_unit*line.product_uom_qty<=rule.to_end:
                                price_unit=-rule.based_on_fixed_price*currency_factor
                            else:
                                order.message_post(body=("<b>Order Amount is not Statisfied Promotion Criteria."))
                                
                    elif rule.price_based_on in ['percentage']:
                        if rule.to_end == -1:
                            if line.price_unit*line.product_uom_qty>=rule.from_start:
                                price=line.price_unit*line.product_uom_qty
                                price_unit=-(price*(rule.based_on_percent_price))/100
                            else:
                                order.message_post(body=("<b>Order Amount is not Statisfied Promotion Criteria."))
                        else:
                            if line.price_unit*line.product_uom_qty>=rule.from_start and line.price_unit*line.product_uom_qty<=rule.to_end:
                                price=line.price_unit*line.product_uom_qty
                                price_unit=-(price*(rule.based_on_percent_price))/100
                            else:
                                order.message_post(body=("<b>Order Amount is not Statisfied Promotion Criteria."))
                                
                                        
            elif promotion.range_based_on in ['qty']:
                
                for rule in promotion.rule_based_ids:
                    if rule.price_based_on in ['fixed']:
                        if rule.to_end == -1:
                            if line.product_uom_qty>=rule.from_start:
                                price_unit=-rule.based_on_fixed_price*currency_factor
                            else:
                                order.message_post(body=("<b>Order Quantity is not Statisfied Promotion Criteria."))
                        else:
                            if line.product_uom_qty>=rule.from_start and line.product_uom_qty<=rule.to_end:
                                price_unit=-rule.based_on_fixed_price*currency_factor
                            else:
                                order.message_post(body=("<b>Order Quantity is not Statisfied Promotion Criteria."))
                                
                    elif rule.price_based_on in ['percentage']:
                        if rule.to_end == -1:
                            if line.product_uom_qty>=rule.from_start:
                                price=line.price_unit*line.product_uom_qty
                                price_unit=-(price*(rule.based_on_percent_price))/100
                            else:
                                order.message_post(body=("<b>Order Quantity is not Statisfied Promotion Criteria."))
                        else:
                            if line.product_uom_qty>=rule.from_start and line.product_uom_qty<=rule.to_end:
                                price=line.price_unit*line.product_uom_qty
                                price_unit=-(price*(rule.based_on_percent_price))/100
                            else:
                                order.message_post(body=("<b>Order Quantity is not Statisfied Promotion Criteria."))
                        
        elif promotion.compute_price in ['bogo_sale']:
            if promotion.bogo_sale_on in ['bxgy']:
                if promotion.bxgy_Aproduct_unit<=line.product_uom_qty:
                    price_unit=-(line.price_unit*promotion.bxgy_Bproduct_unit)
                    line.write({'promotion_product':True})  
                else:
                    price_unit=0.0
                    order.message_post(body=("<b>Order Quantity is not Statisfied Promotion Criteria."))
                    
            elif promotion.bogo_sale_on in ['bogelse']:
                if promotion.bogoelse_Aproduct_unit<=line.product_uom_qty:
                    price_unit=-(promotion.free_product.lst_price*promotion.bogoelse_Bproduct_unit)
                    line.write({'promotion_product':True}) 
                else:
                    price_unit=0.0
                    order.message_post(body=("<b>Order Quantity is not Statisfied Promotion Criteria."))
                    
            elif promotion.bogo_sale_on in['promo_on_prdct_B']:
                cnt=0
                for oline in order.order_line:
                    if oline.product_id.id==promotion.Bproduct.id:
                        if line.product_uom_qty>=promotion.Aproduct_unit:
                            if oline.product_uom_qty>=promotion.Bproduct_unit:
                                cnt+=1
                                if promotion.promo_on_prdct_B_on in ['fixed_price']:
                                    price_unit=-(promotion.promo_on_prdct_B_fixed_price*currency_factor)
                                    oline.write({'promotion_price':price_unit,'promotion_product':True})
                                if promotion.promo_on_prdct_B_on in ['percentage']:
                                    price=oline.price_unit*oline.product_uom_qty
                                    price_unit =-(price*(promotion.promo_on_prdct_B_percentage_price))/100
                                    oline.write({'promotion_price':price_unit,'promotion_product':True})
                            else:
                                price_unit=0.0
                                order.message_post(body=("<b>Sorry,Discount Product Quantity is not Satisfied Promotion Criteria.</b>"))

                        else:
                            price_unit=0.0
                            order.message_post(body=("<b>Sorry,Product Quantity is not Satisfied Promotion Criteria.</b>"))
                if cnt==0:
                    price_unit=0.0
                    order.message_post(body=("<b>Promotion Product is not in your Sale Order.</b>"))                   
                                           
        if promotion.compute_price in ['other_promotionlist'] and price!=0.0:
            price_unit=price+price_unit
        return price_unit
    @api.multi
    def action_view_saleorders(self):
        self.ensure_one()
        action = self.env.ref('promotion_ept.action_sale_order_list')
        
        return {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'view_type': action.view_type,
            'view_mode': action.view_mode,
            'target': action.target,
            'res_model': action.res_model,
            'domain': [('promotion_id', '=', self.id),('state','in',('sale','done'))],
        }
        
    @api.multi
    def action_view_saleorders_line(self):
        self.ensure_one()
        action = self.env.ref('promotion_ept.action_sale_order_line_list')
        
        return {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'view_type': action.view_type,
            'view_mode': action.view_mode,
            'target': action.target,
            'res_model': action.res_model,
            'domain': [('order_id.promotion_id', '=', self.id),('promotion_price','<',0),('order_id.state','in',('sale','done'))],
        }
        
    @api.multi
    def action_view_quotationorders(self):
        self.ensure_one()
        action = self.env.ref('promotion_ept.action_sale_quotation_list')
        
        return {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'view_type': action.view_type,
            'view_mode': action.view_mode,
            'target': action.target,
            'res_model': action.res_model,
            'domain': [('promotion_id', '=', self.id),('state','not in',('sale','done','cancel'))],
        }
        
    @api.multi
    def action_view_quotationorders_line(self):
        self.ensure_one()
        action = self.env.ref('promotion_ept.action_sale_quotation_line_list')
        
        return {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'view_type': action.view_type,
            'view_mode': action.view_mode,
            'target': action.target,
            'res_model': action.res_model,
            'domain': [('order_id.promotion_id', '=', self.id),('promotion_price','<',0),('order_id.state','not in',('sale','done','cancel'))],
        } 