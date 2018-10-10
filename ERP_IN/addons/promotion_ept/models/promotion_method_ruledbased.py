import odoo
from odoo import fields,models,api,_
from odoo.exceptions import ValidationError

class promotion_method_ruledbased(models.Model):
    
    _name='promotion.method.rule.based'
    
    promo_id = fields.Many2one('promotion.method', string='Promotion Reference', ondelete='cascade', index=True)
    from_start=fields.Float('Start')
    to_end=fields.Float('End')
    price_based_on=fields.Selection([
        ('fixed', 'Fix Price'),
        ('percentage', 'Percentage (discount)')], index=True, default='fixed')
    based_on_fixed_price = fields.Float('Fixed Price', default=0.0)
    based_on_percent_price = fields.Float('Percentage Price', default=0.0)
    
    @api.constrains('to_end','from_start','price_based_on','based_on_fixed_price','based_on_percent_price')
    def _check_something(self):
        '''
            This method use for validation at promotion create time.
        '''
        for record in self:
            if record.based_on_percent_price > 99:
                raise ValidationError("It has to be less then 100")
            if record.to_end <= -2 or record.from_start <= -2 or record.to_end == 0 or record.from_start==0:
                raise ValidationError("Please enter valid Start or End number")
            if record.price_based_on in ['fixed']:
                if record.based_on_fixed_price<=0.0:
                    raise ValidationError("Please enter Some Value for Calculation")
            if record.price_based_on in ['percentage']:
                if record.based_on_percent_price<=0.0:
                    raise ValidationError("Please enter Some Value for Calculation")
       
class PromotionExtend(models.TransientModel):
    _name='promotion.extend'
    
    end_date = fields.Date('End Date', help="Ending date of promotion code",required=True)
    
    @api.multi
    def extend_promotion(self):
        '''
            This method use for extend end date of promotion.
        '''
        self = self.with_context(key='promotion_extend')
        promotion=self.env['promotion.method'].browse(self._context.get('active_ids'))
        promotion.write({'date_end':self.end_date})
        return True

        