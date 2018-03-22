import os, shutil
import re, time, datetime
import requests

from django.http import HttpResponse
from django.db import IntegrityError
from django.db.models import Sum
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.utils.translation import ugettext
from django.views.decorators.csrf import csrf_exempt

from pa3_web.forms import SubscribeForm, BlacklistForm
from pa3.models import WaitingNumberBatch, WaitingNumber, NewestNumberBatch, StatisticalData
from pa3.settings import USER_TO_NAMES, RECOGNIZER_AUTH, OPENINGS, BASE_DIR


from pa3_web.views import index

import logging
logger = logging.getLogger('web')
logger_sub = logging.getLogger('subscribe')


def call_clients(payload, protocol='', meta={}):
    return []


def subscribe_client(request):
    logger.debug("subscribe_client")
    if request.method == 'POST':
        form = SubscribeForm(request.POST.get('protocol',''),request.POST)
        if form.is_valid():
            if not form.data['recipient']:
                return    #browser, ergo javascript. Nothing to do here
            payload = { 'action' : 'subscribe',
                        'recipient' : form.data['recipient'],
                        'number' : form.data['number'],
                        'buf' : form.data['buf'],
                        'src' : form.data['src'],
                        'lang' : request.META.get('HTTP_ACCEPT_LANGUAGE','en')[:2]}
            for (ret, output) in call_clients(payload, protocol=form.protocol, meta=request.META):
                if not ret:
                    form.add_form_error(output)
                else:
                    form.success.append(output)
        else:
            logger.info(str(form.errors))
    else:
        form = None

    return index(request, subscribeform=form)


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

    logger.info('{} {} {} {}'.format(src, ts, begin_ts, numbers))
    if not src or not ts or not begin_ts or len(numbers) != len(USER_TO_NAMES[src]):
        return HttpResponse(status=400, content='did not validate!\n')

    request_ip = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if not request_ip:
        request_ip = request.META.get('REMOTE_ADDR', '')

    # get todays opening times for validation
    date_ = datetime.datetime.fromtimestamp(ts)
    for i_ in OPENINGS:
        if date_.isoweekday() == i_['weekday']:
            opening_time = i_
            break
    else:
        opening_time = None

#    if not opening_time or 'begin' not in opening_time or \
#        opening_time['begin'] > int(date_.strftime('%H%M')) or \
#        opening_time['end'] < int(date_.strftime('%H%M'))-60:    #60min buffer
#
    print(numbers, ts, src)

    num_batch_newest, old_num_batch = _get_old_batches(src)
    old_numbers = list(old_num_batch.numbers.all()) if old_num_batch else []
    new_batch = None
    for num, _src in zip(numbers, USER_TO_NAMES[src]):

        old_num_obj = None
        if old_num_batch is not None:
            old_number_ = [i for i in old_numbers if i.src == _src]
            if old_number_:
                old_num_obj = old_number_[0]
                if old_num_obj.number == num:
                    # if number stays or comes outside of the opening times, just update
                    continue

        # compute delta, if not first DB-Entry
        new_number_date_delta = ts - old_num_obj.date if old_num_obj else -1
        new_num_obj = WaitingNumber(number=num, src=_src, date=ts,
                                    date_delta=new_number_date_delta,
                                    proc_delay=time.time() - begin_ts)
        new_num_obj.save()

        if not new_batch:
            # proc_delay will be set after EVERYTHING else
            new_batch = WaitingNumberBatch(src=src, src_ip=request_ip, date=ts, proc_delay=None,
                                           date_delta=ts-old_num_batch.date if old_num_batch else -1)
            new_batch.save()
            [new_batch.numbers.add(i) for i in old_numbers]

        [new_batch.numbers.remove(i) for i in old_numbers if i.src == _src]
        new_batch.numbers.add(new_num_obj)

        if new_number_date_delta < (opening_time['end']-opening_time['begin'])*60:
            # Update Stats if num is not first of the day, e.g. date_delta < openings
            _update_stats(_src, new_number_date_delta, new_batch, ts)

        # update clients. -1 means no change. Use API for initial values
        payload = {'action': 'number',
                   'number': str(num),
                   'src': _src,
                   'ts': str(ts)
                   }
        call_clients(payload)

    if num_batch_newest is None:
        num_batch_newest = NewestNumberBatch(src=src, newest=old_num_batch)
    if new_batch:
        new_batch.proc_delay = time.time() - begin_ts
        new_batch.save()
        # replace NewestNumberBatch
        num_batch_newest.newest = new_batch

    num_batch_newest.date = ts
    num_batch_newest.save()

    return HttpResponse(status=201)


def _update_stats(_src, dd, new_batch, ts):
    try:
        stat_ = StatisticalData.objects.get(src=_src)
        stat_.avg_sum += dd
        stat_.avg_len += 1
        # sum/len = avg | sum=avg*len | new_avg = sum+dd/len+1
        stat_.avg = 1.0 * stat_.avg_sum / stat_.avg_len
        stat_.avg_whole = (stat_.avg + stat_.avg_last_two_weeks + stat_.avg_last_same_day) / 3

        if new_batch.proc_delay > 0:
            stat_.avg_proc_delay_sum += new_batch.proc_delay
            stat_.avg_proc_delay_len += 1
            stat_.avg_proc_delay_whole = 1.0 * stat_.avg_proc_delay_sum / stat_.avg_proc_delay_len

        stat_.date = ts
        stat_.save()
    except MultipleObjectsReturned:
        for stats_ in StatisticalData.objects.filter(src=_src):
            stats_.delete()
    except ObjectDoesNotExist:
        real_data_begin = int(datetime.date(2013, 9, 1).strftime("%s"))
        stat_ = StatisticalData(src=_src, date=ts)
        stat_qs = WaitingNumber.objects.filter(src=_src).filter(date__gt=real_data_begin).filter(
            date_delta__lt=60 * 60 * 3).filter(date_delta__gt=1)
        stat_.avg_len = stat_qs.count()
        stat_.avg_sum = stat_qs.aggregate(s=Sum('date_delta'))['s']
        stat_.avg = 1.0 * stat_.avg_sum / stat_.avg_len
        stat_.avg_last_two_weeks = stat_.avg
        stat_.avg_last_same_day = stat_.avg
        stat_.avg_whole = (stat_.avg + stat_.avg_last_two_weeks + stat_.avg_last_same_day) / 3

        stat_.avg_proc_delay_sum = stat_qs.aggregate(s=Sum('proc_delay'))['s']
        stat_.avg_proc_delay_whole = 1.0 * stat_.avg_proc_delay_sum / stat_.avg_len

        stat_.save()

    except Exception as e:
        logger.exception('Exception while updating Stats: {}'.format(e))


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


def recompute_stats(request):
    # Recomputes the last_two_weeks average and the last_day average
    # Requires calls, e.g. CRON
    real_data_begin = int(datetime.date(2013,5,1).strftime("%s"))

    for stat_data in StatisticalData.objects.all():
        # Get average over the last two weeks
        last_two_weeks_qs = WaitingNumber.objects.filter(src=stat_data.src).filter(date__gt=real_data_begin).filter(date_delta__lt=60*60*3).filter(date_delta__gt=1).filter(date__gt=int(time.time())-(60*60*24*14))
        last_two_weeks_len = last_two_weeks_qs.count()
        stat_data.avg_last_two_weeks = last_two_weeks_qs.aggregate(s=Sum('date_delta'))['s'] / last_two_weeks_len if last_two_weeks_len else 0

        # Get average from weekday last week (Tuesday last week)
        now = int(datetime.date.today().strftime('%s'))
        weekday_range = (now - (60*60*24*7), now + (24*60*60) - (60*60*24*7))
        last_sameday_qs = WaitingNumber.objects.filter(src=stat_data.src).filter(date__gt=real_data_begin).filter(date_delta__lt=60*60*3).filter(date_delta__gt=1).filter(date__range=weekday_range)
        last_sameday_len = last_sameday_qs.count()
        stat_data.avg_last_same_day = last_sameday_qs.aggregate(s=Sum('date_delta'))['s'] / last_sameday_len if last_sameday_len else 0

        # Weights of whole, last two weeks and last weekday are equal
        if last_two_weeks_len and last_sameday_len:
            stat_data.avg_whole = (stat_data.avg + stat_data.avg_last_two_weeks + stat_data.avg_last_same_day) / 3.0
        elif last_two_weeks_len:
            stat_data.avg_whole = (stat_data.avg + stat_data.avg_last_two_weeks) / 2.0
        elif last_sameday_len:
            stat_data.avg_whole = (stat_data.avg + stat_data.avg_last_same_day) / 2.0
        else:
            stat_data.avg_whole = stat_data.avg

        stat_data.save()
    return HttpResponse(status=200)
