$('.chat[data-chat=mwon724]').addClass('active-chat');
$('.person[data-chat=mwon724]').addClass('active');

$('.left .person').mousedown(function(){
    if ($(this).hasClass('.active')) {
        return false;
    } else {
        var findChat = $(this).attr('data-chat');
        var personName = $(this).find('.name').text();
        $('.right .top .name').html(personName);
        $('.chat').removeClass('active-chat');
        $('.left .person').removeClass('active');
        $(this).addClass('active');
        $('.chat[data-chat = '+findChat+']').addClass('active-chat');
        $('.chat.active-chat').scrollTop($('.chat.active-chat')[0].scrollHeight);
    }
});

$('.chat.active-chat').scrollTop($('.chat.active-chat')[0].scrollHeight);