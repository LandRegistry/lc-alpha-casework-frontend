// Custom image pan/zoom control. This one will do what we need of it.
// TODO: consider animation

var PannerControl = {
    pannerInfo: {},
    rootElement: null,
    currentIndex: 0,
    buttonDown: false,
    offset: {x: 0, y: 0},
    initial: {x: 0, y: 0},
    currentImage: null,
    zoomButton: null,

    init: function(rootElement, zoomButton) {
        var zoom = zoomButton;
        zoom.addEventListener('click', PannerControl.zoomButtonClick);
        PannerControl.rootElement = rootElement;
        PannerControl.zoomButton = zoomButton;

        var divs = rootElement.querySelectorAll('.image_panner');
        for( var i = 0; i < divs.length; i++ ) {
            var panner = divs[i];

            // set some styles up...
            panner.style.width = '100%';
            panner.style.height = '100%';
            panner.style.overflow = 'hidden';
            if( i !== PannerControl.currentIndex ) {
                panner.style.display = 'none';
            } else {
                panner.style.display = 'block';
            }

            var image = panner.querySelector('img');
            if(panner.getAttribute('id') && image) {
                var ar = image.height / image.width;
                var size = {
                    'x': panner.parentElement.clientWidth,
                    'y': panner.parentElement.clientWidth * ar
                }

                var info = {
                    'ar': image.height / image.width,
                    'zoomed': false,
                    'img': image,
                    'width': panner.parentElement.clientWidth,
                    'offset': {
                        'x': 0,
                        'y': 0
                    },
                    'size': size,
                    'limits': {
                        'x': panner.parentElement.clientWidth - size.x,
                        'y': panner.parentElement.parentElement.clientHeight - size.y
                    }
                };

                if(i === PannerControl.currentIndex) {
                    PannerControl.currentImage = info;
                }

                image.style.left = '0px';
                image.style.top = '0px';
                image.style.position = 'relative';

                image.style.width = rootElement.clientWidth + 'px';
                PannerControl.pannerInfo[panner.getAttribute('id')] = info;

                panner.addEventListener('mousedown', PannerControl.mouseDown);
                panner.addEventListener('mouseup', PannerControl.mouseUp);
                panner.addEventListener('mouseout', PannerControl.mouseUp);
                panner.addEventListener('mousemove', PannerControl.mouseMove);
            }
        }
    },

    showImage: function(index) {
        var divs = PannerControl.rootElement.querySelectorAll('.image_panner');
        divs[PannerControl.currentIndex].style.display = 'none';
        PannerControl.currentIndex = index;
        divs[PannerControl.currentIndex].style.display = 'block';

        PannerControl.currentImage = PannerControl.pannerInfo[
            divs[PannerControl.currentIndex].getAttribute('id')
        ];

        PannerControl.zoomButton.classList.remove('zoom_button_in', 'zoom_button_out');
        if(PannerControl.currentImage['zoomed']) {
            PannerControl.zoomButton.classList.add('zoom_button_out');


        } else {
            PannerControl.zoomButton.classList.add('zoom_button_in');
        }
    },


    mouseDown: function(e) {
        e.preventDefault();
        PannerControl.buttonDown = true;
        PannerControl.initial.x = parseInt(PannerControl.currentImage['img'].style.left);
        PannerControl.initial.y = parseInt(PannerControl.currentImage['img'].style.top);

        PannerControl.offset.x = e.x;
        PannerControl.offset.y = e.y;
    },

    mouseUp: function(e) {
        PannerControl.buttonDown = false;
    },

    mouseMove: function(e) {
        e.preventDefault();
        if(PannerControl.buttonDown) {
            var Δx = e.x - PannerControl.offset.x;
            var Δy = e.y - PannerControl.offset.y;

            var left = PannerControl.initial.x + Δx;
            var top = PannerControl.initial.y + Δy;

            var lim = PannerControl.currentImage['limits'];

            if(left < lim.x) {left=lim.x;}
            if(top < lim.y) {top=lim.y;}


            if(left > 0) {
                left = 0;
            }

            if(top > 0) {
                top = 0;
            }

            PannerControl.currentImage['img'].style.left = left + 'px';
            PannerControl.currentImage['img'].style.top = top + 'px';
        }
    },

    zoomButtonClick: function(e) {
        var divs = PannerControl.rootElement.querySelectorAll('.image_panner');
        var id = divs[PannerControl.currentIndex].getAttribute('id');

        var panner = divs[PannerControl.currentIndex];

        // for now, just zoom - do we animate? have jQuery anyway...
        //  ... but for animating non-CSS properties, Velocity.js is more fun
        var image = PannerControl.pannerInfo[id];

        if(image.zoomed) {
            size = {
                'x': panner.parentElement.clientWidth,
                'y': panner.parentElement.clientWidth * image['ar']
            }
            image['img'].style.width = PannerControl.rootElement.clientWidth + 'px';
            image['width'] = panner.parentElement.clientWidth;
            image['size'] = size;
            image['limits'] = {
                'x': panner.parentElement.clientWidth - size.x,
                'y': panner.parentElement.parentElement.clientHeight - size.y
            }
            image['img'].style.left = '0px';
            image['img'].style.top = '0px';
            PannerControl.zoomButton.classList.remove('zoom_button_out');
            PannerControl.zoomButton.classList.add('zoom_button_in');

            image.zoomed = false;
        } else {
            var newWidth = image['width'] * 2;
            var newHeight = newWidth * image['ar'];

            image['img'].style.width = newWidth + 'px';

            var left = parseInt(image['img'].style.left);
            var top = parseInt(image['img'].style.top);

            left -= (newWidth / 4);
            top -= (newHeight / 4);

            image['img'].style.left = left + 'px';
            image['img'].style.top = top + 'px';

            image['width'] = newWidth;

            // calc size and limits
            image['size'] = {
                'x': newWidth,
                'y': newHeight
            };

            image['limits'] = {
                'x': panner.parentElement.clientWidth - image['size'].x,
                'y': panner.parentElement.parentElement.clientHeight - image['size'].y
            };
            PannerControl.zoomButton.classList.remove('zoom_button_in');
            PannerControl.zoomButton.classList.add('zoom_button_out');
            image.zoomed = true;
        }
    }
};