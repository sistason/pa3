import time, pytz, os

from django.http import HttpResponse

from django.core.files.storage import FileSystemStorage
from django.utils.translation import ugettext
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from pa3_web.models import Subscriber
from pa3.models import WaitingNumberBatch, WaitingNumber, NewestNumberBatch
from pa3.settings import USER_TO_NAMES, RECOGNIZER_AUTH, OPENINGS, IMAGE_DESTINATION, TIME_ZONE

from pa3 import statistics_handling

import logging


logger = logging.getLogger('web')
logger_sub = logging.getLogger('subscribe')


@csrf_exempt
def write(request):
    if not request.POST or not {'user', 'password', 'ts',
                                'numbers', 'begin'}.issubset(request.POST):
        logger.info("received an invalid write request: %s" % request)
        return HttpResponse(status=401, content='POST request incomplete!\n')

    if request.POST.get('user') not in USER_TO_NAMES.keys() or \
            RECOGNIZER_AUTH != request.POST.get('password'):
        logger.info("received an unauthorized write request: %s" % request)
        return HttpResponse(status=401, content="permission denied!\n")

    #---------------------- validating input ---------------------

    numbers = []
    for number in request.POST.get('numbers', '').strip().split(' '):
        if number.isdigit():
            numbers.append(int(number))
        else:
            numbers.append(-1)

    try:
        ts=int(request.POST.get('ts', 0))
        begin_ts=float(request.POST.get('begin', 0.0))
    except ValueError:
        ts = 0
        begin_ts = 0.0

    src = request.POST.get('user')
    displays = USER_TO_NAMES.get(src, {}).get('displays', [])

    if not src or not ts or not begin_ts or len(numbers) != len(displays):
        return HttpResponse(status=400, content='did not validate!\n')

    request_ip = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if not request_ip:
        request_ip = request.META.get('REMOTE_ADDR', '')

    # get todays opening times for validation
    date_ = timezone.datetime.fromtimestamp(ts, tz=pytz.timezone(TIME_ZONE))
    for i_ in OPENINGS:
        if date_.isoweekday() == i_['weekday']:
            opening_time = i_
            break
    else:
        opening_time = None

    num_batch_newest, old_num_batch = _get_old_batches(src)
    old_numbers = list(old_num_batch.numbers.all()) if old_num_batch else []
    new_batch = None
    for num, _src in zip(numbers, displays):

        old_num_obj = None
        if old_num_batch is not None:
            old_number_ = [i for i in old_numbers if i.src == _src]
            if old_number_:
                old_num_obj = old_number_[0]
                if old_num_obj.number == num or num == -1:
                    # if number stays or comes outside of the opening times, just update
                    continue
                #    if not opening_time or 'begin' not in opening_time or \
                #        opening_time['begin'] > int(date_.strftime('%H%M')) or \
                #        opening_time['end'] < int(date_.strftime('%H%M'))-60:    #60min buffer
                #       continue

        # compute delta, if not first DB-Entry
        new_number_date_delta = (date_ - old_num_obj.date).seconds if old_num_obj else -1
        src_statistic = statistics_handling.get_src_statistic(_src)
        if src_statistic is None:
            src_statistic = statistics_handling.create_statistic(_src, date_)
        new_num_obj = WaitingNumber(number=num, src=_src, date=date_,
                                    date_delta=new_number_date_delta,
                                    proc_delay=time.time() - begin_ts,
                                    statistic=src_statistic)
        new_num_obj.save()

        if not new_batch:
            # proc_delay will be set after EVERYTHING else
            new_batch = WaitingNumberBatch(src=src, src_ip=request_ip, date=date_, proc_delay=None,
                                           date_delta=(date_-old_num_batch.date).seconds if old_num_batch else -1)
            new_batch.save()
            [new_batch.numbers.add(i) for i in old_numbers]

        [new_batch.numbers.remove(i) for i in old_numbers if i.src == _src]
        new_batch.numbers.add(new_num_obj)

        if new_number_date_delta < (opening_time.get('end', 0)-opening_time.get('begin', 0))*60:
            # Update Stats if num is not first of the day, e.g. date_delta < openings
            statistics_handling.update_statistic(_src, new_number_date_delta, new_batch, date_)

        for subscriber in Subscriber.objects.filter(src=_src, protocol='sms'):
            subscriber.handle(num)

    if num_batch_newest is None:
        num_batch_newest = NewestNumberBatch(src=src, newest=old_num_batch)
    if new_batch:
        new_batch.proc_delay = time.time() - begin_ts
        new_batch.save()
        # replace NewestNumberBatch
        num_batch_newest.newest = new_batch

    num_batch_newest.date = date_
    num_batch_newest.save()

    if request.FILES and 'raw_image' in request.FILES.keys():
        _save_image(request, src)

    return HttpResponse(status=201)


def _save_image(request, src):
    image = request.FILES.get('raw_image')
    extension = os.path.splitext(image.name)[-1]
    image_name = "{}{}".format(src, extension)

    fs = FileSystemStorage(location=IMAGE_DESTINATION)
    filename = fs.save(image_name, image)
    if fs.exists(image.name):
        os.rename(os.path.join(IMAGE_DESTINATION, filename), os.path.join(IMAGE_DESTINATION, image_name))


def _get_old_batches(src):
    num_batches_newest = NewestNumberBatch.objects.filter(src=src)
    if num_batches_newest.exists():
        num_batch_newest = num_batches_newest.latest('date')
        old_num_batch = num_batch_newest.newest
    else:
        num_batches = WaitingNumberBatch.objects.filter(src=src)
        if num_batches.exists():
            old_num_batch = num_batches.latest('date')
        else:
            old_num_batch = None

        num_batch_newest = None
    return num_batch_newest, old_num_batch
