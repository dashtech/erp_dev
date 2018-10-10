/*
    Part of Odoo Module Developed by 73lines
    See LICENSE file for full copyright and licensing details.
*/

window.setInterval(function(){
    if ($('li.add_to_cart_js').length && $('li.price_js').hasClass('active')) {
        $('li.add_to_cart_js').addClass('hidden');
    } else {
        $('li.add_to_cart_js').removeClass('hidden');
    }
}, 1000);
