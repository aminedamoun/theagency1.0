(function (window, document, $, undefined) {
    'use strict';

    var aiwaveJs = {
        i: function (e) {
            aiwaveJs.d();
            aiwaveJs.methods();
        },

        d: function (e) {
            this._window = $(window),
            this._document = $(document),
            this._body = $('body'),
            this._html = $('html')
        },
        
        methods: function (e) {
            aiwaveJs.smothScroll();
            aiwaveJs.counterUpActivation();
            aiwaveJs.wowActivation();
            aiwaveJs.headerTopActivation();
            aiwaveJs.headerSticky();
            aiwaveJs.salActive();
            aiwaveJs.popupMobileMenu();
            aiwaveJs.popupDislikeSection();
            aiwaveJs.popupleftdashboard();
            aiwaveJs.popuprightdashboard();
            aiwaveJs.preloaderInit();
            aiwaveJs.showMoreBtn();
            aiwaveJs.slickSliderActivation();
            aiwaveJs.radialProgress();
            aiwaveJs.contactForm();
            aiwaveJs.menuCurrentLink();
            aiwaveJs.onePageNav();
            aiwaveJs.selectPicker();
        },



        selectPicker: function () {
            $('select').selectpicker();
        },


        menuCurrentLink: function () {
            var path = location.pathname
                        
            $('.dashboard-mainmenu li a').each(function(){
                var $this = $(this);
                if($this.attr('href') === path){
                    $this.addClass('active');
                    $this.parents('.has-menu-child-item').addClass('menu-item-open')
                }
            });
            $('.mainmenu li a').each(function(){
                var $this = $(this);
                if($this.attr('href') === path){
                    $this.addClass('active');
                    $this.parents('.has-menu-child-item').addClass('menu-item-open')
                }
            });
            $('.user-nav li a').each(function(){
                var $this = $(this);
                if($this.attr('href') === path){
                    $this.addClass('active');
                    $this.parents('.has-menu-child-item').addClass('menu-item-open')
                }
            });
        },



        smothScroll: function () {
            $(document).on('click', '.smoth-animation', function (event) {
                event.preventDefault();
                $('html, body').animate({
                    scrollTop: $($.attr(this, 'href')).offset().top - 50
                }, 300);
            });
        },


        popupMobileMenu: function (e) {
            $('.hamberger-button').on('click', function (e) {
                $('.popup-mobile-menu').addClass('active');
            });

            $('.close-menu').on('click', function (e) {
                $('.popup-mobile-menu').removeClass('active');
                $('.popup-mobile-menu .mainmenu .has-dropdown > a, .popup-mobile-menu .mainmenu .with-megamenu > a').siblings('.submenu, .rainbow-megamenu').removeClass('active').slideUp('400');
                $('.popup-mobile-menu .mainmenu .has-dropdown > a, .popup-mobile-menu .mainmenu .with-megamenu > a').removeClass('open')
            });

            $('.popup-mobile-menu .mainmenu .has-dropdown > a, .popup-mobile-menu .mainmenu .with-megamenu > a').on('click', function (e) {
                e.preventDefault();
                $(this).siblings('.submenu, .rainbow-megamenu').toggleClass('active').slideToggle('400');
                $(this).toggleClass('open')
            })

            $('.popup-mobile-menu, .popup-mobile-menu .mainmenu.onepagenav li a').on('click', function (e) {
                e.target === this && $('.popup-mobile-menu').removeClass('active') && $('.popup-mobile-menu .mainmenu .has-dropdown > a, .popup-mobile-menu .mainmenu .with-megamenu > a').siblings('.submenu, .rainbow-megamenu').removeClass('active').slideUp('400') && $('.popup-mobile-menu .mainmenu .has-dropdown > a, .popup-mobile-menu .mainmenu .with-megamenu > a').removeClass('open');
            });
        },

        popupDislikeSection: function(e){
            $('.dislike-section-btn').on('click', function (e) {
                $('.popup-dislike-section').addClass('active');
            });

            $('.close-button').on('click', function (e) {
                $('.popup-dislike-section').removeClass('active');
            });
        },

        popupleftdashboard: function(e){
            function updateSidebar() {
                if ($(window).width() >= 1600) {
                    $('.popup-dashboardleft-btn').removeClass('collapsed');
                    $('.popup-dashboardleft-section').removeClass('collapsed');
                } else {
                    $('.popup-dashboardleft-btn').addClass('collapsed');
                    $('.popup-dashboardleft-section').addClass('collapsed');
                }
            }

            // Hide sidebars by default
            $('.popup-dashboardleft-btn, .popup-dashboardleft-section, .rbt-main-content, .rbt-static-bar').hide();

            // Initial setup on page load
            updateSidebar();

            // Show sidebars after determining the appropriate state
            $('.popup-dashboardleft-btn, .popup-dashboardleft-section, .rbt-main-content, .rbt-static-bar').show();
        
            // Update on window resize
            $(window).on('resize', function () {
                updateSidebar();
            });
        
            // Toggle classes on button click
            $('.popup-dashboardleft-btn').on('click', function (e) {
                $('.popup-dashboardleft-btn').toggleClass('collapsed');
                $('.popup-dashboardleft-section').toggleClass('collapsed');
            });
        },

        popuprightdashboard: function(e){
            function updateSidebar() {
                if ($(window).width() >= 1600) {
                    $('.popup-dashboardright-btn').removeClass('collapsed');
                    $('.popup-dashboardright-section').removeClass('collapsed');
                } else {
                    $('.popup-dashboardright-btn').addClass('collapsed');
                    $('.popup-dashboardright-section').addClass('collapsed');
                }
            }
            // Hide sidebars by default
            $('.popup-right-btn, .popup-right-section, .rbt-main-content, .rbt-static-bar').hide();

            // Initial setup on page load
            updateSidebar();

            // Show sidebars after determining the appropriate state
            $('.popup-right-btn, .popup-right-section, .rbt-main-content, .rbt-static-bar').show();
        
            // Update on window resize
            $(window).on('resize', function () {
                updateSidebar();
            });
        
            // Toggle classes on button click
            $('.popup-dashboardright-btn').on('click', function (e) {
                $('.popup-dashboardright-btn').toggleClass('collapsed');
                $('.popup-dashboardright-section').toggleClass('collapsed');
            });
        },

        
        preloaderInit: function(){
            aiwaveJs._window.on('load', function () {
                $('.preloader').fadeOut('slow', function () {
                    $(this).remove();
                });
            });
        },
        
        showMoreBtn: function () {
            $.fn.hasShowMore = function () {
                return this.each(function () {
                    $(this).toggleClass('active');
                    $(this).text('Show Less');
                    $(this).parent('.has-show-more').toggleClass('active');

                    
                    if ($(this).parent('.has-show-more').hasClass('active')) {
                        $(this).innerHTML('Show Less');
                    } else {
                        $(this).text('Show More');
                    }
                    
                });
            };
            $(document).on('click', '.rbt-show-more-btn', function () {
                $(this).hasShowMore();
            });
        },


        

        slickSliderActivation: function () {
            $('.testimonial-activation').not('.slick-initialized').slick({
                infinite: true,
                slidesToShow: 1,
                slidesToScroll: 1,
                dots: true,
                arrows: true,
                adaptiveHeight: true,
                cssEase: 'linear',
                prevArrow: '<button class="slide-arrow prev-arrow"><i class="fa-regular fa-arrow-left"></i></button>',
                nextArrow: '<button class="slide-arrow next-arrow"><i class="fa-sharp fa-regular fa-arrow-right"></i></button>'
            });

            $('.sm-slider-carosel-activation').not('.slick-initialized').slick({
                infinite: true,
                slidesToShow: 1,
                slidesToScroll: 1,
                dots: true,
                arrows: false,
                adaptiveHeight: true,
                cssEase: 'linear',
            });

            $('.slider-activation').not('.slick-initialized').slick({
                infinite: true,
                slidesToShow: 1,
                slidesToScroll: 1,
                dots: true,
                arrows: true,
                adaptiveHeight: true,
                cssEase: 'linear',
                prevArrow: '<button class="slide-arrow prev-arrow"><i class="fa-regular fa-arrow-left"></i></button>',
                nextArrow: '<button class="slide-arrow next-arrow"><i class="fa-sharp fa-regular fa-arrow-right"></i></button>'
            });

            $('.blog-carousel-activation').not('.slick-initialized').slick({
                infinite: true,
                slidesToShow: 3,
                slidesToScroll: 1,
                dots: true,
                arrows: false,
                adaptiveHeight: true,
                cssEase: 'linear',
                responsive: [
                    {
                      breakpoint: 769,
                        settings: {
                            slidesToShow: 2,
                            slidesToScroll: 2
                        }
                    },
                    {
                        breakpoint: 581,
                        settings: {
                            slidesToShow: 1,
                            slidesToScroll: 1
                        }
                    }
                  ]
            });

            $('.rainbow-service-slider-actvation').not('.slick-initialized').slick({
                infinite: true,
                slidesToShow: 3,
                slidesToScroll: 2,
                dots: true,
                arrows: true,
                prevArrow: '<button class="slide-arrow prev-arrow"><i class="fa-regular fa-arrow-left"></i></button>',
                nextArrow: '<button class="slide-arrow next-arrow"><i class="fa-sharp fa-regular fa-arrow-right"></i></button>',
                cssEase: 'linear',
                responsive: [
                    {
                      breakpoint: 1200,
                        settings: {
                            slidesToShow: 2,
                            slidesToScroll: 1
                        }
                    },
                    {
                      breakpoint: 992,
                        settings: {
                            slidesToShow: 2,
                            slidesToScroll: 1
                        }
                    },
                    {
                      breakpoint: 769,
                        settings: {
                            slidesToShow: 1,
                            slidesToScroll: 1
                        }
                    },
                    {
                        breakpoint: 581,
                        settings: {
                            slidesToShow: 1,
                            slidesToScroll: 1
                        }
                    }
                  ]
            });

            $('.slider-brand-activation').not('.slick-initialized').slick({
                centerMode: true,
                draggable: false,
                centerPadding: '150px',
                dots: false,
                arrows: false,
                infinite: true,
                slidesToShow: 4,
                slidesToScroll: 1,
                autoplay: true,
                autoplaySpeed: 0,
                speed: 8000,
                pauseOnHover: true,
                cssEase: 'linear',
                responsive: [
                    {
                    breakpoint: 1200,
                    settings: {
                        arrows: false,
                        centerMode: true,
                        centerPadding: '40px',
                        slidesToShow: 4,
                    }
                    },
                    {
                    breakpoint: 992,
                    settings: {
                        arrows: false,
                        centerMode: true,
                        centerPadding: '40px',
                        slidesToShow: 3,
                    }
                    },
                    {
                    breakpoint: 768,
                    settings: {
                        arrows: false,
                        centerMode: true,
                        centerPadding: '40px',
                        slidesToShow: 2,
                    }
                    },
                    {
                    breakpoint: 480,
                    settings: {
                        arrows: false,
                        centerMode: true,
                        centerPadding: '40px',
                        slidesToShow: 1
                    }
                    }
                ]
            });


            $('.brand-carousel-activation').not('.slick-initialized').slick({
                infinite: true,
                slidesToShow: 6,
                slidesToScroll: 1,
                dots: true,
                arrows: true,
                adaptiveHeight: true,
                cssEase: 'linear',
                prevArrow: '<button class="slide-arrow prev-arrow"><i class="fa-regular fa-arrow-left"></i></button>',
                nextArrow: '<button class="slide-arrow next-arrow"><i class="fa-sharp fa-regular fa-arrow-right"></i></button>',
                responsive: [
                    {
                      breakpoint: 769,
                        settings: {
                            slidesToShow: 4,
                            slidesToScroll: 2
                        }
                    },
                    {
                        breakpoint: 581,
                        settings: {
                            slidesToShow: 3,
                        }
                    },
                    {
                        breakpoint: 480,
                        settings: {
                            slidesToShow: 2,
                        }
                    },
                  ]
            });

            $('.banner-imgview-carousel-activation').not('.slick-initialized').slick({
                infinite: true,
                slidesToShow: 5,
                slidesToScroll: 1,
                dots: false,
                autoplay: true,
                arrows: false,
                adaptiveHeight: true,
                centerMode:true,
                centerPadding: '100px',
                cssEase: 'linear',
                prevArrow: '<button class="slide-arrow prev-arrow"><i class="fa-regular fa-arrow-left"></i></button>',
                nextArrow: '<button class="slide-arrow next-arrow"><i class="fa-sharp fa-regular fa-arrow-right"></i></button>',
                responsive: [
                    {
                      breakpoint: 769,
                        settings: {
                            slidesToShow: 3,
                            slidesToScroll: 2
                        }
                    },
                    {
                        breakpoint: 581,
                        settings: {
                            slidesToShow: 3,
                        }
                    },
                    {
                        breakpoint: 480,
                        settings: {
                            slidesToShow: 2,
                        }
                    },
                  ]
            });

            $('.vedio-popup-carousel-activation').not('.slick-initialized').slick({
                infinite: true,
                slidesToShow: 1,
                slidesToScroll: 1,
                dots: false,
                autoplay: false,
                arrows: false,
                adaptiveHeight: true,
                centerMode:true,
                centerPadding: '200px',
                cssEase: 'linear',
                prevArrow: '<button class="slide-arrow prev-arrow"><i class="fa-regular fa-arrow-left"></i></button>',
                nextArrow: '<button class="slide-arrow next-arrow"><i class="fa-sharp fa-regular fa-arrow-right"></i></button>',
                responsive: [
                    {
                      breakpoint: 769,
                        settings: {
                            slidesToShow: 2,
                            slidesToScroll: 1
                        }
                    },
                    {
                        breakpoint: 581,
                        settings: {
                            slidesToShow: 2,
                        }
                    },
                    {
                        breakpoint: 480,
                        settings: {
                            slidesToShow: 2,
                        }
                    },
                  ]
            });

            $('.brand-carousel-init').not('.slick-initialized').slick({
                infinite: true,
                slidesToShow: 5,
                slidesToScroll: 1,
                dots: false,
                arrows: true,
                adaptiveHeight: true,
                cssEase: 'linear',
                prevArrow: '<button class="slide-arrow prev-arrow"><i class="fa-regular fa-arrow-left"></i></button>',
                nextArrow: '<button class="slide-arrow next-arrow"><i class="fa-sharp fa-regular fa-arrow-right"></i></button>',
                responsive: [
                    {
                      breakpoint: 769,
                        settings: {
                            slidesToShow: 4,
                            slidesToScroll: 2
                        }
                    },
                    {
                        breakpoint: 581,
                        settings: {
                            slidesToShow: 3,
                        }
                    },
                    {
                        breakpoint: 480,
                        settings: {
                            slidesToShow: 2,
                        }
                    },
                  ]
            });


            $('.about-app-activation').not('.slick-initialized').slick({
                infinite: true,
                slidesToShow: 1,
                slidesToScroll: 1,
                dots: true,
                arrows: false,
                adaptiveHeight: true,
                cssEase: 'linear',
                prevArrow: '<button class="slide-arrow prev-arrow"><i class="fa-regular fa-arrow-left"></i></button>',
                nextArrow: '<button class="slide-arrow next-arrow"><i class="fa-sharp fa-regular fa-arrow-right"></i></button>',
            });



            $('.template-galary-activation').not('.slick-initialized').slick({
                infinite: true,
                slidesToShow: 3,
                slidesToScroll: 1,
                dots: true,
                arrows: true,
                adaptiveHeight: true,
                cssEase: 'linear',
                centerMode: false,
                prevArrow: '<button class="slide-arrow prev-arrow"><i class="fa-regular fa-arrow-left"></i></button>',
                nextArrow: '<button class="slide-arrow next-arrow"><i class="fa-sharp fa-regular fa-arrow-right"></i></button>',
                responsive: [
                    {
                      breakpoint: 769,
                        settings: {
                            slidesToShow: 4,
                            slidesToScroll: 2
                        }
                    },
                    {
                        breakpoint: 581,
                        settings: {
                            slidesToShow: 3,
                        }
                    },
                    {
                        breakpoint: 480,
                        settings: {
                            slidesToShow: 2,
                        }
                    },
                  ]
            });




        },

        salActive: function () {
            sal({
                threshold: 0.01,
                once: true,
            });
        },

        backToTopInit: function () {
            var scrollTop = $('.rainbow-back-top');
            $(window).scroll(function () {
                var topPos = $(this).scrollTop();
                if (topPos > 150) {
                    $(scrollTop).css('opacity', '1');
                } else {
                    $(scrollTop).css('opacity', '0');
                }
            });
            $(scrollTop).on('click', function () {
                $('html, body').animate({
                    scrollTop: 0,
                    easingType: 'linear',
                }, 10);
                return false;
            });
        },

        headerSticky: function () {
            $(window).scroll(function () {
                if ($(this).scrollTop() > 250) {
                    $('.header-sticky').addClass('sticky')
                } else {
                    $('.header-sticky').removeClass('sticky')
                }
            })
        },

        counterUpActivation: function () {
            $('.counter').counterUp({
                delay: 10,
                time: 1000
            });
        },

        wowActivation: function () {
            new WOW().init();
        },

        headerTopActivation: function () {
            $('.bgsection-activation').on('click', function () {
                $('.header-top-news').addClass('deactive')
            })
        },

        radialProgress: function () {
            $('.radial-progress').waypoint(function () {
                $('.radial-progress').easyPieChart({
                    lineWidth: 10,
                    scaleLength: 0,
                    rotate: 0,
                    trackColor: false,
                    lineCap: 'round',
                    size: 220
                });
            }, {
                triggerOnce: true,
                offset: 'bottom-in-view'
            });
        },


        contactForm: function () {
            $('.rainbow-dynamic-form').on('submit', function (e) {
				e.preventDefault();
				var _self = $(this);
				var __selector = _self.closest('input,textarea');
				_self.closest('div').find('input,textarea').removeAttr('style');
				_self.find('.error-msg').remove();
				_self.closest('div').find('button[type="submit"]').attr('disabled', 'disabled');
				var data = $(this).serialize();
				$.ajax({
					url: 'mail.php',
					type: "post",
					dataType: 'json',
					data: data,
					success: function (data) {
						_self.closest('div').find('button[type="submit"]').removeAttr('disabled');
						if (data.code == false) {
							_self.closest('div').find('[name="' + data.field + '"]');
							_self.find('.rainbow-btn').after('<div class="error-msg"><p>*' + data.err + '</p></div>');
						} else {
							$('.error-msg').hide();
							$('.form-group').removeClass('focused');
							_self.find('.rainbow-btn').after('<div class="success-msg"><p>' + data.success + '</p></div>');
							_self.closest('div').find('input,textarea').val('');

							setTimeout(function () {
								$('.success-msg').fadeOut('slow');
							}, 5000);
						}
					}
				});
			});
        },

        onePageNav: function () {
            $('.onepagenav').onePageNav({
                currentClass: 'current',
                changeHash: false,
                scrollSpeed: 500,
                scrollThreshold: 0.2,
                filter: '',
                easing: 'swing',
            });
        },
    }
    aiwaveJs.i();

})(window, document, jQuery)


// Bg flashlight
    let cards = document.querySelectorAll('.bg-flashlight')
    cards.forEach(bgflashlight => {
        bgflashlight.onmousemove = function(e){
            let x = e.pageX - bgflashlight.offsetLeft;
            let y = e.pageY - bgflashlight.offsetTop;

            bgflashlight.style.setProperty('--x', x + 'px');
            bgflashlight.style.setProperty('--y', y + 'px');
        }
    });

// Bg flashlight
let shapes = document.querySelectorAll('.blur-flashlight')
shapes.forEach(bgflashlight => {
    bgflashlight.onmousemove = function(e){
        let x = e.pageX - bgflashlight.offsetLeft;
        let y = e.pageY - bgflashlight.offsetTop;

        bgflashlight.style.setProperty('--x', x+70 + 'px');
        bgflashlight.style.setProperty('--y', y+200 +'px');
    }
});




// Tooltip
var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
  return new bootstrap.Tooltip(tooltipTriggerEl)
});


// Expand Textarea
// function expandTextarea(id) {
//     document.getElementById(id).addEventListener('keyup', function() {
//         this.style.overflow = 'hidden';
//         this.style.height = 0;
//         this.style.height = this.scrollHeight + 'px';
//     }, false);
// }

// expandTextarea('txtarea');





//Check All JS Activation
$(function() {
    var propFn = typeof $.fn.prop === 'function' ? 'prop' : 'attr';

    $('#checkall').click(function() {
        $(this).parents('fieldset:eq(0)').find(':checkbox')[propFn]('checked', this.checked);
    });
    $("input[type=checkbox]:not(#checkall)").click(function() {
        if (!this.checked) {
            $("#checkall")[propFn]('checked', this.checked);
        } else {
            $("#checkall")[propFn]('checked', !$("input[type=checkbox]:not(#checkall)").filter(':not(:checked)').length);
        }

    });
});




// Unified error handling for signup and signin forms
function showFormError(input, message) {
    const inputSection = input.closest('.input-section');
    let error = inputSection.nextElementSibling;
    if (!error || !error.classList.contains('input-error')) {
        error = document.createElement('div');
        error.className = 'input-error';
        error.style.color = 'red';
        error.style.fontSize = '13px';
        error.style.marginTop = '2px';
        inputSection.parentNode.insertBefore(error, inputSection.nextSibling);
    }
    error.textContent = message;
}
function clearFormError(input) {
    const inputSection = input.closest('.input-section');
    let error = inputSection.nextElementSibling;
    if (error && error.classList.contains('input-error')) {
        error.textContent = '';
    }
}

['signup', 'signin'].forEach(function(actionType) {
    var form = document.querySelector('form[action*="' + actionType + '"]');
    if (form) {
        form.addEventListener('submit', function (e) {
            let valid = true;
            const name = form.querySelector('input[name="username"], input[placeholder*="Name"]');
            const email = form.querySelector('input[type="email"], input[name="email"]');
            const password = form.querySelectorAll('input[type="password"], input[name="password"]')[0];
            const confirmPassword = form.querySelectorAll('input[type="password"], input[name="confirm_password"]')[1];
            // Name check (only for signup)
            if (name && actionType === 'signup') {
                clearFormError(name);
                if (!name.value.trim()) {
                    showFormError(name, 'Name is required.');
                    valid = false;
                }
            }
            // Email check
            if (email) {
                clearFormError(email);
                const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!email.value.trim()) {
                    showFormError(email, 'Email is required.');
                    valid = false;
                } else if (!emailPattern.test(email.value.trim())) {
                    showFormError(email, 'Enter a valid email address.');
                    valid = false;
                }
            }
            // Password check
            if (password) {
                clearFormError(password);
                if (!password.value) {
                    showFormError(password, 'Password is required.');
                    valid = false;
                } else if (password.value.length < 6) {
                    showFormError(password, 'Password must be at least 6 characters.');
                    valid = false;
                }
            }
            // Confirm password check (only for signup)
            if (confirmPassword && actionType === 'signup') {
                clearFormError(confirmPassword);
                if (!confirmPassword.value) {
                    showFormError(confirmPassword, 'Please confirm your password.');
                    valid = false;
                } else if (password && password.value !== confirmPassword.value) {
                    showFormError(confirmPassword, 'Passwords do not match.');
                    valid = false;
                }
            }
            if (!valid) e.preventDefault();
        });
        // Clear error on input
        form.querySelectorAll('input').forEach(input => {
            input.addEventListener('input', () => clearFormError(input));
        });
    }
});


    // Chat Box Reply

    const txtarea = document.getElementById('txtarea');
    const chatContainer = document.getElementById('chatContainer');
    const sessionListEl = document.getElementById('sessionList');
    const newChatButton = document.getElementById('newChatBtn');  
    const newChatBtn = document.getElementById('newChatBtn');
    const messageFeedbackState = {};
    const botMode = window.BOT_MODE

    // Initialize controller for aborting fetch requests
    let abortController = null;
    // Track the current chat session ID
    let currentSessionId = null;
    let feedbackTargetMessageId = null;
    let feedbackType = null;
    let userMessage = '';

    // On page load, set currentSessionId from window.INITIAL_SESSION_ID if present
    if (window.INITIAL_SESSION_ID) {
        currentSessionId = window.INITIAL_SESSION_ID;
    }

    async function generateAutoReply(userMessage, sessionId) {
        try {
            const fd = new FormData();
            fd.append('chatMessage', userMessage);
            fd.append('sessionId', sessionId);
            fd.append('botMode', window.BOT_MODE || 'text');

            const response = await fetch('/aiwave/text-generator/', {
                method: 'POST',
                body: fd,
                headers: {
                    'X-CSRFToken': csrftoken,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (!response.ok){
                handleError('Error generating reply:', error);
                throw new Error('Network response was not ok');
            }
            const data = await response.json();

            // Return the generated text from the backend
            return data
        } catch (error) {
            handleError('Error generating reply:', error);
            return {
                generated_text: "Sorry, there was an error generating a response.",
                message_id: null
            };
        }
    }

    function resetchatContainer() {
        if (!chatContainer) return; // Prevent error if element is missing
        chatContainer.innerHTML = '<div class="placeholder flex items-center justify-center h-full min-h-[300px] text-neutral-500 dark:text-neutral-400" style="height:100%;min-height:345px;">Start a new conversation by typing a message below.</div>';
        if (txtarea) {
            txtarea.value = '';
            txtarea.placeholder = 'Message AiWave...';
        }
    }

    function groupSessionsByDate(sessions) {
        const now = new Date();
        const oneDayMs = 24 * 60 * 60 * 1000;

            return sessions.reduce((buckets, session) => {
              const d = new Date(session.modified_at);
              const diffDays = Math.floor((now - d) / oneDayMs);
            
              let label;
              if (diffDays === 0) {
                label = 'Today';
              } else if (diffDays === 1) {
                label = 'Yesterday';
              } else if (diffDays <= 7) {
                label = 'Last 7 days';
              } else if (diffDays <= 30) {
                label = 'Last 30 days';
              } else if (d.getFullYear() === now.getFullYear()) {
                label = 'Earlier this year';
              } else {
                label = 'Last year';
              }
            
              if (!buckets[label]) buckets[label] = [];
              buckets[label].push(session);
              return buckets;
        }, {});
    }
      
          /**
           * Fetch all chat sessions from the server and render them.
           * Groups sessions by date headers, then lists each session.
           */

    async function fetchSessions() {
        if (!sessionListEl) return;
        try {
            const res = await fetch(`/aiwave/get-sessions/?botMode=${encodeURIComponent(botMode)}`);
            if (!res.ok) throw new Error(res.statusText);
            const { sessions } = await res.json();

            sessionListEl.innerHTML = '';

            if (!sessions.length) {
                sessionListEl.innerHTML = '<li class="text-neutral-600">No sessions available</li>';
                return;
            }

            // Group sessions by date
            const grouped = groupSessionsByDate(sessions);

            // Flatten all sessions for modal use
            const allSessionItems = [];
            Object.entries(grouped).forEach(([bucketLabel, items]) => {
                items.forEach(s => allSessionItems.push({ ...s, group: bucketLabel }));
            });

            // Show only first 8 sessions in the sidebar
            let shown = 0;
            let showMoreInserted = false;
            Object.entries(grouped).forEach(([bucketLabel, items]) => {
                const visibleItems = items.slice(0, Math.max(0, 8 - shown));
                if (!visibleItems.length || shown >= 8) return;
                const section = document.createElement('div');
                section.className = 'chat-history-section';

                // Date header
                const header = document.createElement('h6');
                header.className = 'title';
                header.textContent = bucketLabel;
                section.appendChild(header);

                // Session list
                const ul = document.createElement('ul');
                ul.className = 'chat-history-list';

                visibleItems.forEach((s, idx) => {
                    if (shown >= 8) return;
                    const li = document.createElement('li');
                    li.className = 'history-box' + (currentSessionId === s.session_id ? ' active' : '');

                    // Session title
                    const titleSpan = document.createElement('span');
                    titleSpan.className = 'session-title';
                    titleSpan.innerHTML = window.marked ? marked.parse(s.title || 'New Conversation') : makeHumanReadable(s.title || 'New Conversation');
                    li.appendChild(titleSpan);

                    // Dropdown for actions
                    const dropdownDiv = document.createElement('div');
                    dropdownDiv.className = 'dropdown history-box-dropdown';
                    dropdownDiv.innerHTML = `
                        <button type="button" class="more-info-icon dropdown-toggle" data-bs-toggle="dropdown" aria-expanded="false">
                            <i class="fa-regular fa-ellipsis"></i>
                        </button>
                        <ul class="dropdown-menu style-one">
                            <li><a class="dropdown-item delete-item" href="#"  onclick="event.preventDefault(); deleteSession('${s.session_id}')"><i class="fa-solid fa-trash-can"></i> Delete Chat</a></li>
                        </ul>
                    `;
                    li.appendChild(dropdownDiv);

                    // Click event for selecting session
                    li.addEventListener('click', (e) => {
                        if (e.target.closest('.dropdown')) return;
                        currentSessionId = s.session_id;
                        fetchMessages(currentSessionId);
                        sessionListEl.querySelectorAll('.history-box').forEach(el => el.classList.remove('active'));
                        li.classList.add('active');
                        
                        // Update titles in main area
                        const mainTitleElement = document.querySelector('.chat-top-bar .title');
                        if (mainTitleElement) {
                            mainTitleElement.textContent = s.title || 'New Conversation';
                        }
                    });

                    ul.appendChild(li);
                    shown++;
                });

                // Only append section if there are visible items
                if (ul.children.length > 0) {
                    section.appendChild(ul);
                    sessionListEl.appendChild(section);
                }
            });

            // Show More button if there are more than 8 sessions
            if (allSessionItems.length > 8) {
                const showMoreBtn = document.createElement('button');
                showMoreBtn.type = 'button';
                showMoreBtn.className = 'btn-default bg-solid-primary d-flex align-items-center justify-content-center mx-auto my-3 px-4 py-3 rounded-2 fw-500 gap-2 show-more-btn';
                showMoreBtn.innerHTML = `
                    <span class="icon"><i class="fa-regular fa-chevron-down"></i></span>
                    <span>Show More</span>
                `;

                showMoreBtn.addEventListener('click', (e) => {
                    // Toggle active class for animation
                    showMoreBtn.classList.toggle('active');
                    openSessionModal();
                });
                sessionListEl.appendChild(showMoreBtn);
            }

            // Modal logic
            function openSessionModal() {
                renderModalSessions(allSessionItems);
                const modal = document.getElementById('sessionModalOverlay');
                modal.style.display = 'block';
                setTimeout(() => modal.classList.add('show'), 10); // for fade effect
                document.body.style.overflow = 'hidden';
            }

            function closeSessionModal() {
                const modal = document.getElementById('sessionModalOverlay');
                const showMoreBtn = document.querySelector('.show-more-btn');

                modal.classList.remove('show');
                if (showMoreBtn) {
                    showMoreBtn.classList.remove('active');
                }

                setTimeout(() => { 
                    modal.style.display = 'none';
                }, 200);

                document.body.style.overflow = '';
            }

            // Modal close button
            document.getElementById('closeSessionModal').onclick = closeSessionModal;

            // Modal backdrop click
            document.getElementById('sessionModalOverlay').addEventListener('mousedown', function(e) {
                if (e.target === this || e.target.classList.contains('modal-backdrop')) closeSessionModal();
            });

            // Render all sessions in modal, grouped
            function renderModalSessions(items) {
                const modalSessionList = document.getElementById('modalSessionList');
                modalSessionList.innerHTML = '';
            
                // Group again for modal (to ensure correct order)
                const modalGroups = {};
                items.forEach(s => {
                    if (!modalGroups[s.group]) modalGroups[s.group] = [];
                    modalGroups[s.group].push(s);
                });
            
                Object.entries(modalGroups).forEach(([bucketLabel, groupItems]) => {
                    // Section header
                    const section = document.createElement('div');
                    section.className = 'chat-history-section';
                
                    const header = document.createElement('h6');
                    header.className = 'title';
                    header.textContent = bucketLabel;
                    section.appendChild(header);
                
                    const ul = document.createElement('ul');
                    ul.className = 'chat-history-list';
                
                    groupItems.forEach(s => {
                        const li = document.createElement('li');
                        li.className = 'history-box' + (currentSessionId === s.session_id ? ' active' : '');
                    

                        // Session title
                        const titleSpan = document.createElement('span');
                        titleSpan.className = 'session-title';
                        titleSpan.innerHTML = window.marked ? marked.parse(s.title || 'New Conversation') : makeHumanReadable(s.title || 'New Conversation');
                        li.appendChild(titleSpan);
                    
                        // Dropdown for actions
                        const dropdownDiv = document.createElement('div');
                        dropdownDiv.className = 'dropdown history-box-dropdown';
                        dropdownDiv.innerHTML = `
                            <button type="button" class="more-info-icon dropdown-toggle" data-bs-toggle="dropdown" aria-expanded="false">
                                <i class="fa-regular fa-ellipsis"></i>
                            </button>
                            <ul class="dropdown-menu style-one">
                                <li><a class="dropdown-item delete-item" href="#"  onclick="event.preventDefault(); deleteSession('${s.session_id}')"><i class="fa-solid fa-trash-can"></i> Delete Chat</a></li>
                            </ul>
                        `;
                        li.appendChild(dropdownDiv);
                    
                        li.addEventListener('click', (e) => {
                            if (e.target.closest('.dropdown')) return;
                            currentSessionId = s.session_id;
                            fetchMessages(currentSessionId);
                            closeSessionModal();
                            // Optionally update chat title bar
                            const chatTitleElement = document.querySelector('.chat-top-bar .title');
                            if (chatTitleElement) {
                                chatTitleElement.textContent = s.title || 'New Conversation';
                            }
                            // Update active styling in sidebar
                            sessionListEl.querySelectorAll('.history-box').forEach(el => el.classList.remove('active'));
                        });
                    
                        ul.appendChild(li);
                    });
                
                    section.appendChild(ul);
                    modalSessionList.appendChild(section);
                });
            }    
        } catch (e) {
            showError('Failed to load sessions.');
            handleError(e);
        }
    }
      
          /**
           * Fetch and render all messages for a given session ID.
           */
    async function fetchMessages(sessionId) {
        try {
            
            const res = await fetch(`/aiwave/get-messages/?sessionId=${sessionId}&botMode=${encodeURIComponent(botMode)}`);
            if (!res.ok) throw new Error(res.statusText);
            const { messages, session_title  } = await res.json();
    
            // Update the chat title in both sidebar and main area
            const sidebarTitleElement = document.querySelector('.chat-sidebar-single h6');
            const mainTitleElement = document.querySelector('.chat-top-bar .title');
            
            if (sidebarTitleElement) {
                sidebarTitleElement.innerHTML = window.marked ? marked.parse(session_title || 'New Conversation') : makeHumanReadable(session_title || 'New Conversation');
            }
            if (mainTitleElement) {
                // Render the title as HTML using marked (Markdown renderer)
                mainTitleElement.innerHTML = window.marked ? marked.parse(session_title || 'New Conversation') : makeHumanReadable(session_title || 'New Conversation');
            }

            chatContainer.innerHTML = ''; // Clear chat pane

            messages.forEach(m => {
                messageFeedbackState[m.message_id] = m.feedback_type || 'none';
                // Map server fields to expected fields
                const sender = m.is_bot_response ? 'AiWave' : 'You';
                const text = m.message;
                const speechClass = m.is_bot_response ? 'ai-speech' : 'author-speech';
                const avatar = m.is_bot_response
                    ? (window.botImageUrl || '/static/images/team/avater.png')
                    : (window.userProfilePic || '/static/images/team/team-01sm.jpg');
                const isEditable = !m.is_bot_response;
            
                const el = isEditable
                    ? createEditableMessage(sender, text, speechClass, avatar)
                    : createMessageWithReactions(sender, text, speechClass, avatar, m.message_id);
            
                appendMessage(el);
            });

            scrollChatToBottom();

            chatContainer.scrollTop = chatContainer.scrollHeight; // Scroll to bottom
        } catch (e) {
            showError('Failed to load messages.');
            handleError(e);
        }
    }

    async function deleteSession(sessionId) {
        try {
            // Confirm before deleting
            if (!confirm('Are you sure you want to delete this chat?')) {
                return;
            }

            const response = await fetch(`/aiwave/delete-session/${sessionId}/`, {
                method: 'DELETE',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken,
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            // If we deleted the current session, reset the chat UI
            if (sessionId === currentSessionId) {
                currentSessionId = null;
                resetchatContainer();

                // Update chat title if it exists
                const chatTitleElement = document.querySelector('.chat-top-bar .title');
                if (chatTitleElement) {
                    chatTitleElement.textContent = 'New Chat';
                }
            }

            // Remove session from list if it exists
            const sessionElement = document.querySelector(`[data-session-id="${sessionId}"]`);
            if (sessionElement) {
                sessionElement.remove();
            }

            // Refresh sessions list
            await fetchSessions();

            // Close modal if it's open
            const modal = document.getElementById('sessionModalOverlay');
            if (modal && modal.classList.contains('show')) {
                modal.classList.remove('show');
                setTimeout(() => {
                    modal.style.display = 'none';
                }, 200);
            }

        } catch (error) {
            handleError('Error deleting session:', error);
            showError('Failed to delete session. Please try again.');
        }
    }


    // Add this helper for the loading bubble
    function appendLoadingBubble() {
        const chatContainer = document.getElementById('chatContainer');
        if (!chatContainer) return;
        // Remove any existing loading bubble first
        const old = chatContainer.querySelector('.aiwave-loading-bubble');
        if (old) old.remove();
        const loadingBubble = document.createElement('div');
        loadingBubble.className = 'chat-box ai-speech aiwave-loading-bubble';
        loadingBubble.innerHTML = `
            <div class="inner">
                <div class="chat-section">
                    <div class="author">
                            <img class="w-100" src="${window.botImageUrl || '/static/images/team/avater.png'}" alt="AiWave">
                    </div>
                    <div class="chat-content">
                        <h6 class="title">AiWave <span class="rainbow-badge-card"><i class="fa-sharp fa-regular fa-check"></i> Bot</span></h6>
                        <div class="aiwave-loader-dots">
                            <span></span><span></span><span></span>
                        </div>
                    </div>
                </div>
            </div>
        `;
        chatContainer.appendChild(loadingBubble);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    function removeLoadingBubble() {
        const chatContainer = document.getElementById('chatContainer');
        if (!chatContainer) return;
        const loadingBubble = chatContainer.querySelector('.aiwave-loading-bubble');
        if (loadingBubble) loadingBubble.remove();
    }

    // Update sendMessage to show/hide loading bubble
    async function sendMessage(e) {
        e.preventDefault();

        userMessage = txtarea.value.trim();
        if (userMessage === '') return;

        // Generate a new session ID if not present
        if (!currentSessionId) {
            try {
                currentSessionId = crypto.randomUUID();
            } catch {
                currentSessionId = ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
                    (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
                );
            }
            // Optionally, clear chat UI for new session
            resetchatContainer();
        }

        const userMessageElement = createEditableMessage('You', userMessage, 'author-speech', window.userProfilePic || '/static/images/team/team-01sm.jpg');
        appendMessage(userMessageElement);

        // Show loading bubble
        appendLoadingBubble();

        const autoReply = await generateAutoReply(userMessage, currentSessionId);

        // Remove loading bubble
        removeLoadingBubble();

        // Ensure bot reply is rendered as HTML (markdown parsed)
        const botReplyHtml = window.marked ? marked.parse(autoReply.generated_text) : makeHumanReadable(autoReply.generated_text);
        const autoReplyElement = createMessageWithReactions('AiWave', botReplyHtml, 'ai-speech', window.botImageUrl ||  '/static/images/team/avater.png', autoReply.message_id);
        appendMessage(autoReplyElement);
        txtarea.value = '';

        fetchSessions();
    }

    function createEditableMessage(title, message, speechClass, imgSrc) {
        const messageElement = createMessageElement(title, message, speechClass, imgSrc, true);
        return messageElement;
    }

    function createMessageWithReactions(title, message, speechClass, imgSrc, messageId) {
        const messageElement = createMessageElement(title, message, speechClass, imgSrc, false, messageId);
        return messageElement;
    }

    function createMessageElement(title, message, speechClass, imgSrc, isEditable, messageId) {
        const isBot = title === 'AiWave'; // or use m.is_bot_response if available
        const displayMessage = isBot ? makeHumanReadable(message) : message;

        const botReplyId = isBot ? `bot-reply-${Date.now()}-${Math.floor(Math.random()*10000)}` : '';

        const messageElement = document.createElement('div');
        messageElement.className = `chat-box ${speechClass}`;
        messageElement.innerHTML = `
        <div class="inner">
            <div class="chat-section">
            <div class="author">
                <img class="w-100" src="${imgSrc}" alt="${title}">
            </div>
            <div class="chat-content">
                <h6 class="title">${title}</h6>
                <p class="${isEditable ? 'editable' : ''}" ${isEditable ? 'contenteditable="true"' : ''}>${displayMessage}</p>
                ${isEditable ? getEditButtons() : getReactionButtons(messageId)}
            </div>
            </div>
        </div>
        `;
        return messageElement;
    }

    function getEditButtons() {
        return `
        
        `;
    }

    function getReactionButtons(messageId) {
        const feedback = messageFeedbackState[messageId] || 'none';
        const likeActive = feedback === 'like' ? 'active' : '';
        const dislikeActive = feedback === 'dislike' ? 'active' : '';
        return `
        <div class="reaction-section">
        <div class="btn-grp">
        <div class="left-side-btn dropup">
            <button  class="react-btn btn-default btn-small btn-border ${likeActive}" onclick="handleFeedbackButtonClick('${messageId}', 'like')"><i class="${likeActive ? 'fa-solid' : 'fa-regular'} fa-thumbs-up"></i></button>
            <button  class="react-btn btn-default btn-small btn-border${dislikeActive}" onclick="handleFeedbackButtonClick('${messageId}', 'dislike')"><i class="${dislikeActive ? 'fa-solid' : 'fa-regular'} fa-thumbs-down"></i></button>
            <button type="button" class="react-btn btn-default btn-small btn-border dropdown-toggle" data-bs-toggle="dropdown" aria-expanded="false">
                <i class="fa-regular fa-ellipsis-vertical"></i>
            </button>
            <ul class="dropdown-menu style-one">
                <li><a class="dropdown-item" href="#" onclick="copyMessage(this); return false;"><i class="fa-sharp fa-solid fa-copy"></i> Copy</a></li>
                <li><a class="dropdown-item delete-item" href="#"><i class="fa-solid fa-trash-can"></i> Delete Chat</a></li>
            </ul>
        </div>
    </div>
        </div>
        `;
    }

    function makeHumanReadable(text) {
        if (!text) return '';

        // First, handle code blocks with language specification
        text = text.replace(/```(\w*)\n([\s\S]*?)```/g, function(_, lang, code) {
            const language = lang || 'plaintext';
            return `<div class="bg-gray-100 dark:bg-gray-800 p-4 rounded my-3 overflow-x-auto">
                <div class="text-xs text-gray-500 mb-2 font-mono">${language}</div>
                <pre class="whitespace-pre-wrap break-words">${escapeHtml(code.trim())}</pre>
            </div>`;
        });

        // Then handle simple code blocks without language
        text = text.replace(/```([\s\S]*?)```/g, function(_, code) {
            return `<div class="bg-gray-100 dark:bg-gray-800 p-4 rounded my-3 overflow-x-auto">
                <pre class="whitespace-pre-wrap break-words">${escapeHtml(code.trim())}</pre>
            </div>`;
        });

        // Inline code
        text = text.replace(/`([^`]+)`/g, function(match, code) {
            return `<code class="bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded text-sm font-mono text-red-600 dark:text-red-300">${escapeHtml(code)}</code>`;
        });

        // Handle HTML content that might be in the text
        text = text.replace(/&lt;(\/?[a-z][a-z0-9]*)&gt;/gi, '<$1>');

        // Headers
        text = text.replace(/^###\s+(.+)$/gm, '<h3 class="text-lg font-semibold mt-4 mb-2">$1</h3>');
        text = text.replace(/^##\s+(.+)$/gm, '<h2 class="text-xl font-bold mt-6 mb-3">$1</h2>');
        text = text.replace(/^#\s+(.+)$/gm, '<h1 class="text-2xl font-bold mt-8 mb-4">$1</h1>');

        // Bold and italic
        text = text.replace(/\*\*([^*]+)\*\*/g, '<strong class="font-semibold">$1</strong>');
        text = text.replace(/\*([^*]+)\*/g, '<em class="italic">$1</em>');

        // Lists - handle both * and - for bullet points
        text = text.replace(/^[\s]*[*\-+]\s+(.+)$/gm, '<li class="mb-1">$1</li>');
        
        // Numbered lists
        text = text.replace(/^[\s]*\d+\.\s+(.+)$/gm, '<li class="mb-1 list-decimal list-inside">$1</li>');
        
        // Handle multi-line list items
        text = text.replace(/(<li[^>]*>.*)(?:\n(?!<li>|\s*[\-*+]\s|\d+\.\s|$))(.*)/g, '$1 $2');
        
        // Wrap list items in <ul> or <ol>
        text = text.replace(/(<li[^>]*>.*<\/li>\n?)+/g, function(match) {
            const isOrdered = match.includes('list-decimal');
            const tag = isOrdered ? 'ol' : 'ul';
            return `<${tag} class="space-y-1 my-2 pl-5">${match}</${tag}>`;
        });

        // Blockquotes
        text = text.replace(/^>\s+(.+)$/gm, '<blockquote class="border-l-4 border-gray-300 dark:border-gray-600 pl-4 my-2 text-gray-600 dark:text-gray-300">$1</blockquote>');

        // Horizontal rule
        text = text.replace(/^[-*_]{3,}$/gm, '<hr class="my-4 border-t border-gray-200 dark:border-gray-700">');

        // Simple JSON formatting (if it looks like JSON)
        text = text.replace(/(\{[\s\S]*?\})/g, function(match) {
            try {
                const obj = JSON.parse(match);
                return `<div class="bg-gray-50 dark:bg-gray-800 p-4 rounded my-3 overflow-x-auto">
                    <div class="text-xs text-gray-500 mb-2 font-mono">JSON</div>
                    <pre class="text-xs">${escapeHtml(JSON.stringify(obj, null, 2))}</pre>
                </div>`;
            } catch (e) {
                return match;
            }
        });

        // Handle paragraphs - split by double newlines
        let parts = text.split(/\n\s*\n/);
        text = parts.map(part => {
            if (!part.trim().startsWith('<') || part.trim().startsWith('<li>')) {
                return `<p class="my-2">${part}</p>`;
            }
            return part;
        }).join('\n');

        // Clean up any empty paragraphs
        text = text.replace(/<p[^>]*>\s*<\/p>/g, '');

        return text;
    }

    // Helper: escape HTML for code blocks and inline code
    function escapeHtml(str) {
        return str.replace(/[&<>"']/g, function (m) {
            return {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#39;'
            }[m];
        });
    }

    


    async function sendFeedback(isRemove = false) {
        const textarea = document.getElementById('feedbackText');
        let feedbackText = '';
        
        if (!isRemove && textarea) {
            feedbackText = textarea.value;
        }

            const response = await fetch('/aiwave/message-feedback/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken,
                },
                body: JSON.stringify({
                    message_id: feedbackTargetMessageId,
                    feedback_type: isRemove ? 'none' : feedbackType,
                    message_feedback: isRemove ? '' : feedbackText
                })
            });
            
        const data = await response.json();

        if (data.success) {
            if (isRemove) {
                messageFeedbackState[feedbackTargetMessageId] = 'none';
            } else {
                messageFeedbackState[feedbackTargetMessageId] = feedbackType;
            }
            document.activeElement.blur();
            $('#likeModal').modal('hide');
            $('#dislikeModal').modal('hide');
            if (textarea) textarea.value = '';


        fetchMessages(currentSessionId);
        }
    }



    function appendMessage(messageElement) {
        const chatContainer = document.getElementById('chatContainer');
        const placeholder = chatContainer.querySelector('.placeholder');
        if (placeholder) placeholder.remove();
        chatContainer.appendChild(messageElement);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    function editMessage(button) {
        const chatContent = button.parentElement.parentElement.parentElement;
        const editable = chatContent.querySelector('.editable');
        editable.contentEditable = 'true';
        editable.focus();
    }

    async function saveAndRegenerateMessage(button) {
        const chatContent = button.parentElement.parentElement.parentElement;
        const editable = chatContent.querySelector('.editable');
        userMessage = editable.textContent.trim();
        editable.contentEditable = 'false';

        // Save the edited message (you can send it to a server, etc.)

        // Regenerate a new message
        const regeneratedMessage = await generateAutoReply(userMessage, currentSessionId);
        const regeneratedMessageElement = createMessageWithReactions('AiWave', regeneratedMessage, 'ai-speech', 'assets/images/team/avater.png');
        appendMessage(regeneratedMessageElement);
    }

    function cancelEdit(button) {
        const chatContent = button.parentElement.parentElement.parentElement;
        const editable = chatContent.querySelector('.editable');
        editable.contentEditable = 'false';
        // Optionally, you can revert the content to the original state
    }

    async function regenerateMessage() {
        const regeneratedMessage = await generateAutoReply(userMessage, currentSessionId);
        const regeneratedMessageElement = createMessageWithReactions('AiWave', regeneratedMessage, 'ai-speech', 'assets/images/team/avater.png');
    }

    function copyMessage(button) {
        const lines = button.closest('.chat-content')?.innerText.split('\n') || [];
        const text = lines.slice(1, -3).join('\n');
        navigator.clipboard.writeText(text)
    }
    
    function handleFeedbackButtonClick(messageId, type) {
        // type: 'like' or 'dislike'
        const currentFeedback = messageFeedbackState[messageId];
        if (!currentFeedback || currentFeedback === 'none') {
            // No feedback yet, open the modal for feedback
            openFeedbackModal(type, messageId);
        } else if (currentFeedback === type) {
            // Already liked/disliked, remove feedback
            feedbackTargetMessageId = messageId;
            feedbackType = 'none';
            sendFeedback(true); // Remove feedback
        } else {
            // Switch feedback type (from like to dislike or vice versa)
            openFeedbackModal(type, messageId);
        }
    }

    // Like/Dislike button handlers
    function likeMessage(messageId) {
        openFeedbackModal('like', messageId);
    }
    function dislikeMessage(messageId) {
        openFeedbackModal('dislike', messageId);
    }

    // Open modal and set target message
    function openFeedbackModal(type, messageId) {
        feedbackTargetMessageId = messageId;
        feedbackType = type;
        if (type === 'like') {
            $('#likeModal').modal('show');
        } else if (type === 'dislike') {
            $('#dislikeModal').modal('show');
        }
    }

    function handleError(context, error) {
        showError(typeof error === 'string' ? error : (error.message || 'An error occurred.'));
    }

    function showError(msg) {
        alert(msg);
    }

    function scrollChatToBottom() {
        const chatContainer = document.getElementById('chatContainer');
        if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    }

    if (newChatBtn) {
        newChatBtn.addEventListener('click', function() {
            currentSessionId = null;
            resetchatContainer();
        });
    }
    if (null != txtarea)  {
        txtarea.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage(e);
            }
        });
    };


if (!window.INITIAL_SESSION_ID) {
    resetchatContainer();
}
fetchSessions();

// Add theme-matching loader CSS
const style = document.createElement('style');
style.innerHTML = `
.aiwave-loader-dots {
    display: flex;
    align-items: center;
    gap: 6px;
    margin: 10px 0 10px 0;
    height: 24px;
}
.aiwave-loader-dots span {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--color-primary, #805AF5);
    opacity: 0.7;
    animation: aiwave-bounce 1.2s infinite both;
}
.aiwave-loader-dots span:nth-child(2) {
    animation-delay: 0.2s;
}
.aiwave-loader-dots span:nth-child(3) {
    animation-delay: 0.4s;
}
@keyframes aiwave-bounce {
    0%, 80%, 100% { transform: scale(0.8); opacity: 0.7; }
    40% { transform: scale(1.2); opacity: 1; }
}
`;
document.head.appendChild(style);

// Helper to get CSRF token from cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Usage: get CSRF token
const csrftoken = getCookie('csrftoken');

// Helper to strip markdown (bold, italics, code, etc.) from session titles
function stripMarkdown(text) {
    if (!text) return '';
    // Remove bold (**text**) and italic (*text* or _text_)
    return text
        .replace(/\*\*(.*?)\*\*/g, '$1')
        .replace(/\*(.*?)\*/g, '$1')
        .replace(/_(.*?)_/g, '$1')
        .replace(/`([^`]+)`/g, '$1')
        .replace(/\[(.*?)\]\(.*?\)/g, '$1'); // [text](link)
}




