$('.chat[data-chat=mwon724]').addClass('active-chat');
$('.person[data-chat=mwon724]').addClass('active');

$('.left .person').mousedown(function(){
    if ($(this).hasClass('.active')) {
        return false;
    } else {
        var findChat = $(this).attr('data-chat');
        personName = $(this).find('.name').text();
        $('.right .top .name').html(personName);
        $('.chat').removeClass('active-chat');
        $('.left .person').removeClass('active');
        $(this).addClass('active');
        $('.chat[data-chat = '+findChat+']').addClass('active-chat');
        $('.chat.active-chat').scrollTop($('.chat.active-chat')[0].scrollHeight);
    }
});

$('.chat.active-chat').scrollTop($('.chat.active-chat')[0].scrollHeight);

$(function() {
    // When the testform is submitted…
    $("#sendChat").submit(function() {
        // post the form values via AJAX…
        var postdata = {message: $("#message").val(), recipient: personName} ;
        $.post('/sendMessage', postdata, function(data) {
            // and set the title with the result
            // $("#title").html(data['title']) ;
           });
        return false ;
        });
    });