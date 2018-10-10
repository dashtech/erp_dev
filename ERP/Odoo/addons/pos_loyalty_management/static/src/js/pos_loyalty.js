odoo.define('pos_loyalty_management.pos_loyalty', function(require) {
    "use strict";

    var screens = require('point_of_sale.screens');
    var models = require('point_of_sale.models');
    var PopUpWidget = require('point_of_sale.popups');
    var gui = require('point_of_sale.gui');
    var Model = require('web.DataModel');
    var core = require('web.core');
    var utils = require('web.utils');

    var QWeb = core.qweb;
    var _t = core._t;
    var round_di = utils.round_decimals;
    var round_pr = utils.round_precision;

    models.load_fields('res.partner', 'wk_loyalty_points');
    models.load_fields('product.product', 'wk_point_for_loyalty');

    models.load_models([{
        model: 'loyalty.management',
        condition: function(self) { return true; },
        fields: ['loyalty_base', 'points', 'purchase', 'minimum_purchase'],
        domain: function(self) { return [['config_active', '=', true]]; },
        loaded: function(self, result) {
            self.db.loyality_product_id = null;
            if (result.length) {
                self.set('loyalty_base', result[0].loyalty_base);
                self.set('loyalty_points', result[0].points);
                self.set('loyalty_purchase', result[0].purchase);
                self.set('loyalty_min_purchase', result[0].minimum_purchase);
            }
        },}], { 'after': 'product.product' });


    var LoyaltyRedeemPopupWidget = PopUpWidget.extend({
        template: 'LoyaltyRedeemPopupWidget',
        
        events: _.extend({}, PopUpWidget.prototype.events, {
            'click #wk_redeem_now': 'loyalty_redeem_now',
        }),
       
        loyalty_redeem_now: function() {
            var self = this;
            var currentOrder = self.pos.get_order();
            var discount_offer = currentOrder.get("discount_offer")
            var voucher_product_id = currentOrder.get("voucherProductId");
            var product = self.pos.db.get_product_by_id(voucher_product_id);
            var client = currentOrder.get('client');
            client.wk_loyalty_points = currentOrder.get('remaining_points');
            currentOrder.add_product(product, { price: -discount_offer });
            currentOrder.set('redeemTaken', true);
            self.gui.close_popup();
        },
    });
    gui.define_popup({ name: 'loyalty_redeem_popup', widget: LoyaltyRedeemPopupWidget });
    
    var AlertMessagePopup = PopUpWidget.extend({
		template: 'AlertMessagePopup',
		show:function(options){
			var self = this;
			self._super(options);
		}
	});
	gui.define_popup({ name: 'alert_message', widget: AlertMessagePopup });

    var CustomerRedeemWidget = screens.ActionButtonWidget.extend({
        template: 'CustomerRedeemWidget',
        button_click: function() {
            var self = this;
            var order = this.pos.get_order();
            var current = this;
            var client = order.get_client();
            var msg;
            if (client) {
                if (order.get_total_with_tax() > 0) {
                    if (!order.get('redeemTaken')) {
                        var loyalty_model = new Model('loyalty.management');
                        loyalty_model.call('get_loyalty_product').fail(function(unused, event) {
                            event.preventDefault();
                            msg = _t('Failed to fetch Loyalty Product, Configure Loyalty Rules!!!');
                            self.loyalty_error_alert(msg);
                        }).done(function(product_id) {
                            if (product_id){
                                self.pos.db.loyality_product_id = product_id;
                                order.set('voucherProductId', product_id);
                                loyalty_model.call('get_customer_loyality', [client.id, order.get_total_with_tax()])
                                .fail(function(unused, event) {
                                    event.preventDefault();
                                    msg = _t('Failed to fetch customer loyalty points');
                                    self.loyalty_error_alert(msg);
                                }).done(function(result) {
                                    var tpoints = result.points;
                                    var discount = result.discount;
                                    if (discount != -1) {
                                        if (discount != 0) {
                                            if (tpoints > 0 && client.wk_loyalty_points > 0) {
                                                var dueTotal = order.get_total_with_tax();
                                                var discount_offer = dueTotal > discount ? discount : dueTotal;
                                                discount_offer = round_di(parseFloat(discount_offer) || 0, current.pos.dp['Product Price']);
                                                order.set('discount_offer', discount_offer);
                                                order.set('remaining_points', result.remaining_points);
                                                order.set('total_points', tpoints);
                                                current.gui.show_popup('loyalty_redeem_popup', {
                                                    'name': client.name,
                                                    'points': tpoints,
                                                    'discount': discount_offer,
                                                });
                                            } else {
                                                self.loyalty_error_alert(_t('Sorry You Cannot Redeem, Because Customer Has 0 Points!!!'));
                                            }
                                        } else {
                                            self.loyalty_error_alert(_t('Sorry, You don`t have enough points to redeem !!!'));
                                        }

                                    } else {
                                        self.loyalty_error_alert(_t('Sorry No Redemption Calculation Found in Loyalty Rule. Please Add Redemption Rule First !!!'));
                                    }
                                });
                            }
                            else
                                self.loyalty_error_alert(_t('Sorry No Active Loyalty Rule Found. Please Create  Loyalty Rule First !!!')); 
                        });
                    } else {
                        self.loyalty_error_alert(_t('Sorry You Have Already Redeemed Fidelity points for this customer!!!'));
                    }
                } else {
                    if (order.orderlines.models.length && order.get('redeemTaken'))
                        self.loyalty_error_alert(_t('Sorry You Have Already Redeemed Fidelity points for this customer!!!'));
                    else
                        self.loyalty_error_alert(_t('Please add some Product(s) First !!!'));
                }
            } else {
                self.gui.show_popup('confirm', {
                    'title': _t('Please select the Customer'),
                    'body': _t('You need to select the customer before redeeming the loyalty points.'),
                    confirm: function() {
                        self.gui.show_screen('clientlist');
                    },
                });
            }
        },
        loyalty_error_alert: function(msg) {
            var self = this;
            self.gui.show_popup('alert_message', {
                'title': _t('Loyalty Redemption Error'),
                'body': msg,
            });
        },
    });
    screens.define_action_button({
        'name': 'loyalty',
        'widget': CustomerRedeemWidget,
        'condition': function() {
            return true;
        },
    });

    var _super = models.Order;
    models.Order = models.Order.extend({
        initialize: function(attributes, options) {
            _super.prototype.initialize.apply(this, arguments);
            this.set({
                redeemTaken: false,
                totalEarnedPoint: 0,
                voucherProductId: 0,
                discount_offer: 0,
                total_points: 0,
                remaining_points: 0,
            });

        },
        remove_orderline: function(line) {
            var product_id = line.product.id;
            if (product_id == this.get('voucherProductId')) {
                this.get('client').wk_loyalty_points = this.get("total_points");
                this.set('redeemTaken', false);
                this.set('total_points', 0);
                this.set('discount_offer', 0);
            }
            _super.prototype.remove_orderline.apply(this, arguments);
        },
        // This is Updated function
        get_loyalty_points: function() {
            var orderLines = this.get_orderlines();
            var total_loyalty = 0;

            var loyalty_base = this.pos.get('loyalty_base');

            if (loyalty_base == 'category') {
                for (var i = 0; i < orderLines.length; i++) {
                    var line = orderLines[i];
                    if (line.product.wk_point_for_loyalty > 0) {
                        total_loyalty += round_pr(line.get_quantity() * line.product.wk_point_for_loyalty, 1);
                    }
                }
            } else {
                var currentOrder = this.pos.get_order();
                var tpointsvalue = currentOrder.get_total_with_tax();
                var points = this.pos.get('loyalty_points');
                var purchase = this.pos.get('loyalty_purchase');
                var minimum_purchase = this.pos.get('loyalty_min_purchase');
                var client = currentOrder.get_client();
                if (client && points && purchase) {
                    if (tpointsvalue >= minimum_purchase) {
                        total_loyalty = this.calculate_loyalty_points(tpointsvalue, purchase, points);
                    }

                }
            }
            return total_loyalty;
        },
        calculate_loyalty_points: function(total, purchase, points) {
            return parseInt(total / purchase) * points;
        },
        validate: function() {
            var client = this.get('client');
            if (client) {
                client.wk_loyalty_points += this.get_loyalty_points() || currentOrder.get('remaining_points');
            }
            _super.prototype.validate.apply(this, arguments);
        },
        export_for_printing: function() {
            var currentOrder = this.pos.get_order();
            var client = currentOrder.get('client');
            var json = _super.prototype.export_for_printing.apply(this, arguments);
            json.wk_loyalty_points = this.get_loyalty_points();
            json.tpoints = currentOrder.get('totalEarnedPoint');
            json.redeemTaken = currentOrder.get('redeemTaken');
            return json;
        },
        export_as_JSON: function() {

            var self = this;
            var currentOrder = self.pos.get_order();
            var json = _super.prototype.export_as_JSON.apply(this, arguments);
            if (currentOrder != undefined) {
                json.wk_loyalty_points = this.get_loyalty_points() || currentOrder.get('remaining_points');
                json.tpoints = currentOrder.get('totalEarnedPoint');
                json.redeemTaken = currentOrder.get('redeemTaken');
                json.remaining_points = currentOrder.get('remaining_points');
            }
            return json;
        },
        
        set_client: function(client) {
			var self = this;
            if(self.get('redeemTaken')){
                self.orderlines.models.forEach(function(line){
                    if (line.product.id == self.pos.db.loyality_product_id){
                        self.remove_orderline(line);
                    }
                });
            }
            _super.prototype.set_client.call(this, client);
        },
    });

    screens.OrderWidget.include({
        update_summary: function() {
            this._super();
            var self = this;
            var order = this.pos.get_order();
            var $loypoints = $(this.el).find('.summary .loyalty-points');

            if (order.get_client()) {
                var points = order.get_loyalty_points();
                var points_total = order.get_client().wk_loyalty_points + points;
                var points_str = this.format_pr(points, 1);
                var total_str = this.format_pr(points_total, 1);
                if (points && points > 0) {

                    points_str = '+' + points_str;
                }
                $loypoints.replaceWith($(QWeb.render('LoyaltyPoints', {
                    widget: this,
                    totalpoints: total_str,
                    wonpoints: points_str
                })));
                $loypoints = $(this.el).find('.summary .loyalty-points');
                $loypoints.removeClass('oe_hidden');
            } else {
                $loypoints.empty();
                $loypoints.addClass('oe_hidden');
            }
        },
    });
});