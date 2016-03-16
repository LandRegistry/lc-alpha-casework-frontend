    function do_nothing() {
      return false;
    }

 HOST = window.location.protocol + "//" + window.location.hostname;

$(document).ready(function() {
    $("#refresh").hide();
    display_list = $('#requested_list').val();
    var refresh_screen = setInterval(function(){ location.href="/get_list?appn=" + display_list;}, 30000);
    $('#work-list').DataTable({info: false, paging: false, searching: false, ordering:false});

    // make table row clickable link to child href
    $('#work-list tbody tr').click(function() {
        var href = $(this).find("a").attr("href");
        if(href) {
            window.location = href;
            clearInterval(refresh_screen);
        }
    });

    // prevent a second click for 10 seconds. :)
    $('.prevent_doubleclick').on('click', 'a' ,function(e) {
      $(e.target).click(do_nothing);
      setTimeout(function(){
        $(e.target).unbind('click', do_nothing);
      }, 10000);
    });
} );