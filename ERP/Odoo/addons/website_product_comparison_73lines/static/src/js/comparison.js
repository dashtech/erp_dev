/*
    Part of Odoo Module Developed by 73lines
    See LICENSE file for full copyright and licensing details.
*/

odoo.define('website_product_comparison_73lines.comparison', function (require) {
    "use strict";

    var ajax = require('web.ajax');
    var core = require('web.core');
    var utils = require('web.utils');
    var Widget = require('web.Widget');
    var website = require('web_editor.base');

    var qweb = core.qweb;
    ajax.loadXML('/website_product_comparison_73lines/static/src/xml/comparison.xml', qweb);

    var ProductFeaturePanel = Widget.extend({
        template: 'product_feature_template',
        events: {
            'click .o_product_panel_header': 'display_panel',
            'click .o_close_wrapper': 'hide_panel'
        },
        init: function() {
            this.product_data = {};
            this.shortlist_product_ids = JSON.parse(utils.get_cookie('shortlist_product_ids') || 'null') || [];
            this.comparelist_product_ids = JSON.parse(utils.get_cookie('comparelist_product_ids') || 'null') || [];
        },
        start: function() {
            var self = this;
            var product_ids = _.union(self.shortlist_product_ids, self.comparelist_product_ids);
            this.load_products(product_ids).then(function(){
                new ProductComparison(self).appendTo('.o_product_feature_panel');
            });
        },
        load_products:function(template_ids) {
            var self = this;
            return ajax.jsonRpc('/shop/get_product_data', 'call', {
                'product_ids': template_ids
            }).then(function (data) {
                _.each(data, function(product) {
                    self.product_data[product.id] = product;
                });
            });
        },
        display_panel: function(e) {
            $('.o_product_panel_content').not($(e.currentTarget).next().toggle()).hide();
        },
        hide_panel: function(e) {
            $(e.currentTarget).closest('.o_product_panel_content').hide();
        },
        animate_clone: function(cart, $elem) {
            cart.find('.o_product_circle').addClass('o_shadow_animation').delay(500).queue(function(){
                $(this).removeClass("o_shadow_animation").dequeue();
            });
            var imgtodrag = $elem.closest('form').find('img').eq(0);
            if (imgtodrag.length) {
                var imgclone = imgtodrag.clone()
                .offset({
                    top: imgtodrag.offset().top,
                    left: imgtodrag.offset().left
                })
                .addClass('o_product_comparison_animate')
                .appendTo($('body'))
                .animate({
                    'top': cart.offset().top - 10,
                    'left': cart.offset().left + 20,
                    'width': 75,
                    'height': 75
                }, 1000, 'easeInOutExpo');

                imgclone.animate({
                    'width': 0,
                    'height': 0
                }, function () {
                    $(this).detach();
                });
            }
        }
    });

    var ProductComparison = Widget.extend({
        template:"product_comparison_template",
        events: {
            'click .o_comparelist_products .o_remove': 'rm_from_comparelist'
        },
        init: function(parent){
            this.parent = parent;
            this.comparelist_product_ids = parent.comparelist_product_ids;
            this.product_compare_limit = 4;
        },
        start:function(){
            var self = this;
            $('.oe_website_sale .o_add_compare').click(function (e){
                self.parent.animate_clone($('#comparelist .o_product_panel_header'), $(this));
                if (self.comparelist_product_ids.length < self.product_compare_limit) {
                    self.add_new_products($(this));
                } else {
                    self.$('.o_comparelist_limit_warning, .o_product_panel_content').show();
                }
            });
            self.display_products(self.comparelist_product_ids);
            $('.o_comparelist_remove').click(function (e) {
                self.rm_from_comparelist(e);
            });
            $("#o_comparelist_table tr").click(function(e){
                $($(this).data('target')).children().slideToggle(100);
                $(this).find('.fa-chevron-down, .fa-chevron-right').toggleClass('fa-chevron-down fa-chevron-right');
            });
        },
        add_new_products:function($el){
            var self = this;
           var template_id = $el.data('template-id');
            self.$('.o_comparelist_warning').hide();
            if (!_.contains(self.comparelist_product_ids, template_id)) {
                self.comparelist_product_ids.push(template_id);
                if(_.has(self.parent.product_data, template_id)){
                   self.display_products([template_id]);
                } else {
                    self.parent.load_products([template_id]).then(function(){
                        self.display_products([template_id]);
                    });
                }
            }
        },
        display_products:function(template_ids) {
            var self = this;
            var category = self.check_product_category(self.parent.product_data[template_ids[0]]);
            if (category) {
                _.each(template_ids, function(res) {
                    self.$('.o_product_panel_empty').hide();
                    var $template = $(qweb.render('product_template', self.parent.product_data[res]));
                    self.$('.o_comparelist_products').append($template);
                    $('.oe_website_sale .a-submit').off('click').on('click', function () {
                        $(this).closest('form').submit();
                    });
                });
                self.update_cookie();
            }
        },
        check_product_category: function(data) {
            var category_ids = $('#comparelist .o_product_row:first').data('category_ids');
            if (category_ids){
                var categories = JSON.parse("[" + category_ids + "]");
                if (!_.intersection(categories, data.public_categ_ids).length) {
                    this.$('.o_product_panel_content, .o_comparelist_warning').show();
                    this.$('#comaprelist_alert').text(data.name);
                    this.comparelist_product_ids = _.without(this.comparelist_product_ids, data.id);
                    return false;
                }
            }
            $('.o_comparelist_warning').hide();
            return true;
        },
        rm_from_comparelist: function(e){
            this.comparelist_product_ids = _.without(this.comparelist_product_ids, $(e.currentTarget).data('template_id'));
            $(e.currentTarget).parents('.o_product_row').remove();
            this.$('.o_comparelist_warning, .o_comparelist_limit_warning').hide();
            this.update_cookie();
        },
        update_cookie: function(){
            document.cookie = 'comparelist_product_ids=' + JSON.stringify(this.comparelist_product_ids) + '; path=/';
            this.update_comparelist_view();
        },
        update_comparelist_view: function() {
            this.$('.o_product_circle').text(this.comparelist_product_ids.length);
            this.$('.o_comparelist_button').hide();
            if (_.isEmpty(this.comparelist_product_ids)) {
                this.$('.o_product_panel_empty').show();
                this.$('.o_comparelist_products').hide();
            } else {
                this.$('.o_comparelist_products').show();
                if (this.comparelist_product_ids.length >=2) {
                    this.$('.o_comparelist_button').show();
                    this.$('.o_comparelist_button a').attr('href', '/shop/compare/?products='+this.comparelist_product_ids.toString());
                }
            }
        }
    });

    website.ready().done(function() {
        if(!$('.oe_website_sale').length) {
            return $.Deferred().reject("DOM doesn't contain '.oe_website_sale'");
        }
        $('.o_livechat_button').addClass('o_livechat_button_extend');
        $(".o_specification_panel").click(function(){
            $(this).parent().find('.panel-body').slideToggle('normal');
            $(this).find('.fa-chevron-right,.fa-chevron-down').toggleClass('fa-chevron-right fa-chevron-down');
        });
        ajax.jsonRpc('/shop/check_product_attributes', 'call', {
            'template': 'website_product_comparison_73lines.add_to_compare_shortlist'
        }).then(function (data) {
            if (data) {
                new ProductFeaturePanel().appendTo('#user_li');
            }
        });
    });

});
