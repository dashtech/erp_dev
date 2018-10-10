/*
    Part of Odoo Module Developed by 73lines
    See LICENSE file for full copyright and licensing details.
*/
odoo.define('website_product_misc_options_73lines.products_price_filter', function (require) {
    "use strict";

    var website_sale = require('website_sale.website_sale');

    $('.oe_website_sale').each(function () {

        var oe_website_sale = this;

        var price_min_range = $(oe_website_sale).find('#price_min_range').attr('value');
        if (!price_min_range) {
            price_min_range = 0.0;
        }

        var price_max_range = $(oe_website_sale).find('#price_max_range').attr('value');
        if (!price_max_range) {
            price_max_range = 0.0;
        }

        var price_min = $(oe_website_sale).find('#price_min').attr('value');
        if (!price_min) {
            price_min = price_min_range;
        }

        var price_max = $(oe_website_sale).find('#price_max').attr('value');
        if (!price_max) {
            price_max = price_max_range;
        }

        $("#price_range").ionRangeSlider({
            type: "double",
            grid: true,
            min: parseFloat(price_min_range),
            max: parseFloat(price_max_range),
            from: parseFloat(price_min),
            to: parseFloat(price_max),
            onFinish: function (data) {
                $(oe_website_sale).find('#price_min').attr('value', data.from);
                $(oe_website_sale).find('#price_max').attr('value', data.to);
                $('form.js_attributes').submit();
            },
        });

    });

});
