odoo.define('responsive_pos.responsive_pos', function (require) {
"use strict";
var chrome = require('point_of_sale.chrome');
var core = require('web.core');
var PosBaseWidget = require('point_of_sale.BaseWidget');
var gui = require('point_of_sale.gui');
var screens = require('point_of_sale.screens');
var _t = core._t;

chrome.Chrome.include({
	build_widgets:function() {
		var self = this;
		if(self.pos.config){
		if(self.pos.config.allow_responsive_screen){
			var i = true;
			var orders = self.pos.get_order();
			var qty = 0;
			if(orders != null){
				var order_lines = orders.get_orderlines();
				if(order_lines){
					for(var i=0;i<order_lines.length;i++){
						qty+=order_lines[i].quantity;
					}
				}
			}
			$(".cart_button").html(qty);
			// if(screen.width < 1200){
			// 	$(".leftpane").hide();
			// }
			// $(".cart_button").click(function(){	
			// 	$(".leftpane").slideToggle("slow");	
			// });
			// $( window ).resize(function() {
			// 	alert(screen.width);
			// // 	if(screen.width < 1200){
			// // 		$(".leftpane").hide();
			// // 	}
			// // 	else{
			// // 		$(".leftpane").show();
			// // 	}
			// });
			$("body").click(function(){
				var orders = self.pos.get_order();
				var qty = 0;
				if(orders != null){
					var order_lines = orders.get_orderlines()
					for(var i=0;i<order_lines.length;i++){
						qty+=order_lines[i].quantity;
					}
				}
				$(".cart_button").html(qty);

			});
		}
	}
		this._super();

	},
});
	var PosOrderRemoveLine = screens.ActionButtonWidget.extend({
        template: 'PosOrderRemoveLine',
        button_click: function(){
        	var self = this;
        	var order = self.pos.get_order();
        	order.remove_orderline(order.get_selected_orderline());
        },
    });
	screens.define_action_button({
        'name': 'POS Order Remove Line',
        'widget': PosOrderRemoveLine,
        'condition': function(){
            return ! this.pos.config.allow_bottom_buttons;
        },
    });
});

