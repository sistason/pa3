var current_numbers;

function update_numbers(){
    $.ajax({
        type: 'GET',
        url: '/current_numbers',
        success: update_changed,
        error: function(a,b,c) {
            current_numbers.forEach(update_updated);
        }
     });
}

function update_updated(batch, updated_){
    var $location = $(".number-box-"+batch.newest.src.replace(' ', '.'));

    console.log('update_updated with ' + batch.newest.src + " - " + updated_)
    if (updated_ === undefined)
        // number was not in update, system is broken!
        $location.find(".updated").text("Something broke! Don't rely on this number.");
    else
        $location.find(".updated").text(updated_);
}

function update_changed(data){
    current_numbers.forEach(function(old_newest_batch){
        console.log("updating batch " + old_newest_batch.newest.placement);
        // get batch for comparision
        var old_batch = old_newest_batch.newest;
        var new_newest_batch = data.find(function f(d){return old_batch.src == d.newest.src});
        if (new_newest_batch){
            console.log('new batch found');
            var new_batch = new_newest_batch.newest;
            var batch_src_encoded = old_batch.src.replace(' ', '.');
            update_updated(new_newest_batch, new_newest_batch.updated);
            // check for changed numbers
            old_batch.numbers.forEach(function(old_number) {
                var new_number = new_batch.numbers.find(function f(d){return old_number.src == d.src});
                var number_src_encoded = old_number.src.replace(' ', '.');
                var $number_box = $(".number-box-" + batch_src_encoded);
                if (new_number && new_number.number != old_number.number){
                    $number_box.find(".number-"+number_src_encoded).text(new_number.number);
                    var $image = $number_box.find(".number-"+number_src_encoded);
                    $image.src = $image.src.split('?').slice(0,-1).join('/') + "?" + new Date().getTime();

                    $number_box.find(".called-"+number_src_encoded).text(new_number.called);

                }
                if (new_number) {
                    $number_box.find(".called-"+number_src_encoded).text(new_number.called);
                }

            });
        }
        else{
            // if the batch is not in the update, update it's update_time
            update_updated(old_newest_batch);
        }
    });
    current_numbers = data;


}