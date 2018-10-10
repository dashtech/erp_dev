//function to fix height of iframe!
var calcHeight = function() {
	var headerDimensions = $('.o_main_navbar').height();
	var headerDimensions_2 = $('header').height();
	var headerDimensions_3 = $('footer').height();

	$('.full-screen-preview__frame').height($(window).height() - headerDimensions - headerDimensions_2 - headerDimensions_3 - 2);
}

$(document).ready(function() {
	calcHeight();
});

$(window).resize(function() {
	calcHeight();
}).load(function() {
	calcHeight();
});