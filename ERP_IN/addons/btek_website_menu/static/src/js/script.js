jQuery(document).ready(function(){
	var h_window   = jQuery(window).height(),
		h_container  = jQuery('main').height(),
		h_login_form = jQuery('.oe_login_form').height(),
		hb_area      = jQuery('#oe_main_menu_navbar');


	setTimeout(function(){
		var h_body = jQuery(document).height(),
			h_intro      = jQuery('.intro').height(),
			h_container_1  = jQuery('main').height();

		if ( h_body > h_window ) {
			// alert( h_body + ' | ' + h_window  + ' | ' + h_container_1 );
			var over = h_body - h_window,
				percent = (over*100)/h_window;
			jQuery('.intro > img').css( 'max-width', (90 - percent)+'%' );
		}

		if ( jQuery('.intro').length ) {
			jQuery('.intro').css( 'margin-top', (h_container_1 - h_intro)/2 );
		}

	}, 300);

	if(hb_area.length) {
        hb_area.find('#nav-content').height(h_window).mCustomScrollbar({
        	scrollbarPosition: "outside",
        	autoDraggerLength: false,
        	scrollInertia: 0
        });
    }
	jQuery('.btek-nav').on('click', function(){
		if ( jQuery('#nav-content').hasClass( "active" ) ) {
			jQuery('#nav-content').removeClass('active');
			jQuery('#oe_main_menu_navbar').removeClass('active');
		} else {
			jQuery('#nav-content').addClass('active');
			jQuery('#oe_main_menu_navbar').addClass('active');
			jQuery('body').removeClass('o_mobile_menu_opened');
		}
	});

	jQuery('.o_mobile_menu_toggle').on('click', function(){
		if ( jQuery('#nav-content').hasClass( "active" ) ) {
			jQuery('#nav-content').removeClass('active');
			jQuery('#oe_main_menu_navbar').removeClass('active');
		}
	});

	if ( jQuery('.oe_login_form').length ) {
		jQuery('.oe_login_form').css( 'margin-top', (h_container - h_login_form)/2 );
	}

	// alert ( h_container );

    /* Custom Menu ERP - Store */
    var o_location = window.location.protocol+'//'+window.location.host;
    if ( jQuery("#mCSB_1_container li a").length ) {
        jQuery("#mCSB_1_container li a:not(:empty)").each( function(){
            var $this = jQuery(this);
            var new_link = o_location + $this.attr("href");
            $this.attr("href", new_link);
        });
	}

    if ( jQuery("#mCSB_1_container li img").length ) {
        jQuery("#mCSB_1_container li img, #mCSB_1_container .mCS_img_loaded").each( function(){
            var $this = jQuery(this);
            var new_src = o_location + $this.attr("src");
            $this.attr("src", new_src);
        });

        jQuery("#mCSB_1_container ul li").addClass( 'small-4 medium-3 large-2' );

        jQuery(".oe_menu_bave_store").on( 'click', function(){
            jQuery(this).find( 'form' ).submit();
        });
    }

});

jQuery(window).load( function(){

    /* Custom Menu ERP */
	if ( jQuery('#mCSB_1').length ) {
        var $menu_html = jQuery('#mCSB_1').html();
        jQuery('#menu_html').val( htmlEntities($menu_html) );
	}

});

function htmlEntities(str) {
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}