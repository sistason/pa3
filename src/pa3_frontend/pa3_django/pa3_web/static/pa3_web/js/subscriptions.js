var subscribed;

function subscription_form_init(){
    var $select = $(".subscription #subscription-src");

    current_numbers.forEach(function (newest_batch) {
        newest_batch.newest.numbers.forEach(function(number_obj){
            console.log(number_obj.src);
            $select.append($('<option>', {
                value: number_obj.src,
                text : number_obj.src
            }));
        });
    });

    $(".subscription-form").submit(subscribe);

}

$(".subscription input[name=protocols]:radio").on("change", subscription_form_protocol_change);
function subscription_form_protocol_change(){
    $(".subscription #subscription-identifier").prop("hidden",
        $(".subscription input[name=protocols]:checked").prop("value") === "Browser");
}

function subscribe(event){
    event.preventDefault();
    var $form = $(".subscribe-box .subscription-form");
    var $response = $(".subscribe-box #subscription-response");
    $response.text();

    var buffer = $form.find("#subscription-buffer").prop('value');
    if (!$.isNumeric(buffer))
        buffer = "5";
    var number = $form.find("#subscription-number").prop('value');
    if (!$.isNumeric(number)) {
        $response.text("You need to supply a valid number!");
        $response.prop("class", "error");
        return;
    }
    var src = $form.find("#subscription-src option:selected").prop('value');
    if (!src){
        $response.text("No office selected!");
        $response.prop("class", "error");
        return;
    }

    $.ajax({
        url: $form.prop('action'),
        type: "GET", //after some problems with csrf...
        data: {
            buffer:buffer,
            number:number,
            src: src,
            protocol: 'browser'
            // csrfmiddlewaretoken: $form.find('input[name=csrfmiddlewaretoken]').prop('value')
        },
        success: function(data){
            var message_alert = get_locale() === 'de' ? 'Erfolgreich abonniert! ' : 'Successfully subscribed!';

            if (!("Notification" in window)) {
                alert(message_alert);
            } else if (Notification.permission === "granted") {
                // If it's okay let's create a notification
                new Notification(message_alert);
            }
            // Otherwise, we need to ask the user for permission
            else if (Notification.permission !== "denied") {
                Notification.requestPermission().then(function (permission) {
                // If the user accepts, let's create a notification
                if (permission === "granted") {
                    new Notification(message_alert);
                }
            });
            }

            $response.text(get_locale() === 'de' ? 'Erfolgreich abonniert!' :
                'Successfully subscribed!');
            $response.prop("class", "success");
            subscribed = data.subscription;
            check_if_subscriber_is_due(subscribed);
        },
        error: function(a,b,c){
            subscribed = undefined;
            $response.text(get_locale() === 'de' ?
                'Keine Verbindung zum Server m&ouml;glich, Benachtigungen sind im Moment nicht möglich!' :
                'Could not reach the server, subscription not possible at the moment!');
            $response.prop("class", "error");
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
    var difference = subscriber.number - number;
    return (-50 <= difference && difference <= subscriber.buffer)
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

function get_locale() {
    var lang = navigator.language.split('-')[0];
    if (lang === 'de')
        return 'de';
    return 'en';
}

function alert_and_delete(subscriber, messages){
    var message = messages[get_locale()];

    if (Notification.permission === "granted") {
        new Notification(message);
        alert(message);
    }
    else
        alert(message);

    if (subscriber)
        console.log(subscriber);
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
