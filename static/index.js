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
    // When message is submitted 
    $("#sendChat").submit(function() {
        // Post values (message, recipient) via AJAX
        var post_data = {message: $("#message").val(), recipient: personName} ;
        $.post('/sendMessage', post_data, function(data) {
           });
        var update_data = {username: personName} ;
        $.post('/updateConversation', update_data, function(conv) {
                $('.chat.active-chat').html(conv); // add new bubble 
                $('.chat.active-chat').scrollTop($('.chat.active-chat')[0].scrollHeight); // scroll to bottom
                $('#message').val(''); // clear input box
           });

        return false ;
        });
    });

window.setInterval(function(){
  var update_data = {username: personName} ;
        $.post('/updateConversation', update_data, function(conv) {
                $('.chat.active-chat').html(conv); // add new bubble 
                $('.chat.active-chat').scrollTop($('.chat.active-chat')[0].scrollHeight); // scroll to bottom
           });
}, 1000);

