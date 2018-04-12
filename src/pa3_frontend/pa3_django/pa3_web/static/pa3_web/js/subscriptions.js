var subscribed;

function update_subscription_form(){
    //TODO: form-select mit src füllen
}

function subscribe(){
    //TODO: form
    //TODO: get_from_form

    var buffer;
    var number;
    var src;

    $.ajax({
        url: "/subscribe",
        type: "POST",
        data: {
            buffer:buffer,
            number:number,
            src: src
        },
        success: function(data){
            subscribed = data.subscriber;
            check_if_subscriber_is_due(data.subscriber);
        },
        error: function(a,b,c){
            subscribed = undefined;
            var message_en = "Could not reach the server, subscription not possible at the moment!";
            var message_de = "Keine Verbindung zum Server möglich, Benachtigungen sind im Moment nicht möglich!";
            alert_and_delete(undefined, {de: message_de, en: message_en})
        }
    });
}

function subscription_init(){
    $.ajax({
        url: "/get_subscriber",
        success: function(data){
            subscribed = data.subscriber;
            check_if_subscriber_is_due(data.subscriber);
        },
        error: function(a,b,c){
            subscribed = undefined;
        }
    });
}

function check_if_subscriber_is_due(subscriber){
    if (subscriber)
        current_numbers.forEach(function(newest_batch){
            newest_batch.newest.numbers.forEach(function(number_obj){
                handle_subscriber(subscriber, number_obj);
            });
        });
}

function check_number_due(subscriber, number){
    return (number - subscriber.buffer >= subscriber.number)
}

function handle_subscriber(subscriber, number_obj){
    if (subscriber && subscriber.src === number_obj.src)
        if (check_number_due(subscriber, number_obj.number))
            notify_subscriber(subscriber, number_obj.number);
}


function notify_subscriber(subscriber, number){

    var message_en = "Hey, your number "+subscriber.number+" will be called shortly! Better get ready :)";
    var message_de = "Hey, deine Nummer "+subscriber.number+" wird gleich dran sein! Mach dich schonmal bereit :)";

    alert_and_delete(subscriber, {de: message_de, en: message_en});
}

function alert_and_delete(subscriber, messages){
    //TODO: get locale
    var message = messages.de;

    alert(message);
    if (subscriber)
        subscribed = undefined;
        delete_subscriber(subscriber);
}

function notify_subscriber_system_error(subscriber, batch){
    if (subscriber && subscriber.src === batch.src){
        var message_en = "Hey, there was a problem with the system. The notification has to end here, sorry, " +
            "better safe than sorry. You can check the website if the problem persists, if not, just resubscribe.";
        var message_de = "Hey, es gab ein Problem mit dem System. Die Benachrichtigung muss hier enden, " +
            "um auf der sicheren Seite zu sein. Schau auf der Webseite nach, ob das Problem weiter besteht, wenn " +
            "nicht, wähle die Benachrichtigung einfach erneut aus.";

        alert_and_delete(subscriber, {de: message_de, en: message_en});
    }
}

function delete_subscriber(subscriber){
    $.ajax("/delete_subscriber");
}
