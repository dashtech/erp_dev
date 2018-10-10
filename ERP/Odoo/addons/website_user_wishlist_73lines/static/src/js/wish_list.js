/*
    Part of Odoo Module Developed by 73lines
    See LICENSE file for full copyright and licensing details.
*/

odoo.define('website_user_wishlist_73lines.wish_list', function (require) {
    "use strict";

    var website = require('website.website');
    var ajax = require('web.ajax');
    var Model = require('web.Model');

    // General Function for removing product from wishlist
    function remove_from_wishlist(prod_id) {
        new Model('user.wishlist').call('search_read', [[]], {'fields': ['product_template_id']}).then(function(datas) {
            for (var i = 0; i < datas.length; i++) {
                var prod_temp_id = datas[i]['product_template_id'][0];
                if (prod_temp_id == prod_id) {
                    var del_id = datas[i]['id'];
                    new Model('user.wishlist').call('unlink', [[del_id]]);
                }
            }
        });
    }

    // Add/Remove product from WishList in Single Product Page
    $(document).on('click', function (ev) {
        // For Adding
        if (($(ev.target).hasClass('js_add_remove_wish_list_json')) && ($(ev.target).hasClass('fa-heart-o'))) {
            ev.preventDefault();
            var product_id = $(ev.target).attr('data-product-id');
            ajax.jsonRpc("/profile/add_to_wishlist/", 'call', {'product_id': product_id})
            $(ev.target).removeClass('fa-heart-o').addClass('fa-heart');
            return;
        }
        // For Removing
        if (($(ev.target).hasClass('js_add_remove_wish_list_json')) && ($(ev.target).hasClass('fa-heart'))) {
            ev.preventDefault();
            var prod_id = $(ev.target).attr('data-product-id');
            remove_from_wishlist(prod_id);
            $(ev.target).removeClass('fa-heart').addClass('fa-heart-o');
            return;
        }
    });

    // This one calls when we remove product from wishlist under My Account
    $('a.remove-wishlist').click(function(){
        var prod_id = $(this).attr('id');
        remove_from_wishlist(prod_id);
        $(this).parent().parent().remove();
    });

    // Add/Remove product from WishList in Product Carousel OR Shop Page
    $(document).on('click', function (ev) {
        // For Adding
        if (($(ev.target).hasClass('easy-shortcuts-wishlist') || $(ev.target).hasClass('easy-shortcuts-wishlist-shop')) && ($(ev.target).hasClass('fa-heart-o'))) {
            ev.preventDefault();
            var product_id = $(ev.target).attr('data-product-id');
            ajax.jsonRpc("/profile/add_to_wishlist/", 'call', {'product_id': product_id})
            $(ev.target).removeClass('fa-heart-o').addClass('fa-heart');
            return;
        }
        // For Removing
        if (($(ev.target).hasClass('easy-shortcuts-wishlist') || $(ev.target).hasClass('easy-shortcuts-wishlist-shop')) && ($(ev.target).hasClass('fa-heart'))) {
            ev.preventDefault();
            var prod_id = $(ev.target).attr('data-product-id');
            remove_from_wishlist(prod_id);
            $(ev.target).removeClass('fa-heart').addClass('fa-heart-o');
            return;
       }
    });

});
