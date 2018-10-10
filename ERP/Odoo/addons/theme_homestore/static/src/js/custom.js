$(document).ready( function() {

					(function($) {
						"use strict";
						function count($this) {
							var current = parseInt($this.html(), 10);
							current = current + 1; /* Where 50 is increment */
							$this.html(++current);
							if (current > $this.data('count')) {
								$this.html($this.data('count'));
							} else {
								setTimeout(function() {
									count($this)
								}, 100);
							}
						}
						$(".stat-count").each(
								function() {
									$(this).data('count',
											parseInt($(this).html(), 10));
									$(this).html('0');
									count($(this));
								});
					})(jQuery);
});
/* hide #back-top first */
$("#back-top").hide();
// fade in #back-top
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




$(document).ready( function() {
	
	function getTimeRemaining(endtime) {
		  var t = Date.parse(endtime) - Date.parse(new Date());
		  var seconds = Math.floor((t / 1000) % 60);
		  var minutes = Math.floor((t / 1000 / 60) % 60);
		  var hours = Math.floor((t / (1000 * 60 * 60)) % 24);
		  var days = Math.floor(t / (1000 * 60 * 60 * 24));
		  return {
		    'total': t,
		    'days': days,
		    'hours': hours,
		    'minutes': minutes,
		    'seconds': seconds
		  };
		}

		function initializeClock(id, endtime) {
		  var clock = document.getElementById(id);
		  console.log(clock);
		  var daysSpan = clock.querySelector('.days');
		  var hoursSpan = clock.querySelector('.hours');
		  var minutesSpan = clock.querySelector('.minutes');
		  var secondsSpan = clock.querySelector('.seconds');

		  function updateClock() {
		    var t = getTimeRemaining(endtime);

		    daysSpan.innerHTML = t.days;
		    hoursSpan.innerHTML = ('0' + t.hours).slice(-2);
		    minutesSpan.innerHTML = ('0' + t.minutes).slice(-2);
		    secondsSpan.innerHTML = ('0' + t.seconds).slice(-2);

		    if (t.total <= 0) {
		      //clearInterval(timeinterval);
		    	
		    	 daysSpan.innerHTML = '00';
				 hoursSpan.innerHTML = '00';
				 minutesSpan.innerHTML = '00';
				 secondsSpan.innerHTML = '00';
		    }
		  }

		  updateClock();
		  var timeinterval = setInterval(updateClock, 1000);
		}
		
		
		
		
		var deadline = new Date(Date.parse(new Date()) + 15 * 24 * 60 * 60 * 1000);
		var deadline1 = new Date(Date.parse(new Date()) + 14 * 24 * 60 * 60 * 1000);
		
		console.log(deadline);
		//console.log(deadline1);
		if($('#clockdiv').length ){
			initializeClock('clockdiv', deadline);
			initializeClock('clockdiv1', deadline1);
		}
	
	
	
});
