$(document).ready(function(){
	   $(window).bind('scroll', function() {
	   var navHeight = $( window ).height() / 3 - 70;
			 if ($(window).scrollTop() > navHeight) {
				 $('.navbar').addClass('navbar-fixed-top');
			 }
			 else {
				 
			
				 $('.navbar').removeClass('navbar-fixed-top ');
				 
				
			 }
		});
	});

$("#back-top").hide();
//fade in #back-top
$(function() {
	$(window).scroll(function() {
		if ($(this).scrollTop() > 100) {
			$('#back-top').fadeIn();
		} else {
			$('#back-top').fadeOut();
		}
	});
	// scroll body to 0px on click
	$('#back-top a').click(function() {
		$('body,html').animate({
			scrollTop : 0
		}, 800);
		return false;
	});
});


$(document).ready(function(){
	$('.oe_website_sale').each(function () {
	    var oe_website_sale = this;

	 var $attr_to_reorder = $('#products_grid_before > form.js_attributes', oe_website_sale);
	    console.log(">>>>>>>>>>1>>>>>>>>>.", $attr_to_reorder);

	    var $categ_to_reorder = $('#products_grid_before > div#categ_main', oe_website_sale);
	    console.log(">>>>>>>>>>2>>>>>>>>>.", $categ_to_reorder);

	    $categ_to_reorder.insertBefore($attr_to_reorder);
	});
});

