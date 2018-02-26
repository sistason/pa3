import os, shutil
import re, time, datetime
import requests

from django.http import HttpResponse
from django.db import IntegrityError
from django.db.models import Sum
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned 
from django.utils.translation import ugettext

from pa3_web.forms import SubscribeForm, BlacklistForm
from pa3.models import WaitingNumberBatch, WaitingNumber, NewestNumberBatch, StatisticalData, ClientHandler
from pa3.settings import PA_INDEX, CLIENT_PASSWORDS, OPENINGS, BASE_DIR


from pa3_web.views import abuse, index

import logging
logger = logging.getLogger('web')
logger_sub = logging.getLogger('subscribe')


def call_clients(payload, protocol='', meta={}):
    #make sure pa2 does not crash whatever happens there.
    logger.debug("Payload for clients: %s" % str(payload))
    _ip = meta.get('HTTP_X_FORWARDED_FOR','') if meta.get('HTTP_X_FORWARDED_FOR','') else meta.get('REMOTE_ADDR','')
    _date = str(datetime.datetime.now())

    clients = ClientHandler.objects.filter(active=True)
    if protocol:
        clients = clients.filter(protocol=protocol)

    ret = []

    for client in clients:
        req = requests.post(client.address, data=payload)
        if req.status_code == 200:
            ret.append((True, ugettext('Success!')))
            logger.debug("Payload successfull for client {0}".format(client.name))
            if payload['action'] != 'number':
                logger_sub.info('Success: {0}|{1}|{2}|{3}'.format(_ip, client.protocol, client.name, str(payload)))
        else:
            ret.append((False, "{0}: {1}".format(ugettext('Fail!'), req.status_code)))
            logger.info("Payload unsuccessfull for client {0}: {1}".format(client.name, req.status_code))
            logger_sub.info('Fail   :{4} - {0}|{1}|{2}|{3}'.format(_ip, client.protocol, client.name,
                                                                   str(payload), req.status_code))
    return ret


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

def blacklist_client(request):
    logger.debug("blacklist_client")
    if request.method == 'POST':
        form = BlacklistForm(request.POST)
        if form.is_valid():
            payload = { 'action'   : 'blacklist',
                        'recipient': form.data['address'],
                        'duration' : str(60*24*7)}
            for (ret, output) in call_clients(payload, protocol=form.data['protocol'], meta=request.META):
                if not ret:
                    form.add_form_error(output)
                else:
                    form.success.append(output)
        else:
            logger.info(str(form.errors))
    else:
        form = None
    return abuse(request, blacklistform=form)

def register_handler(request):
    logger.debug("Register_handler")
    if request.method == 'POST' and request.is_secure():
        try:        
            handler = ClientHandler.objects.get(
                                    name=request.POST.get('name',''), 
                                    protocol=request.POST.get('protocol',''))
        except (MultipleObjectsReturned, ObjectDoesNotExist):
            logger_sub.debug('Handler {1}:{0} does not exist!'.format(
                        request.POST.get('name',''),request.POST.get('protocol','')))
            return HttpResponse(status=418, content="I'm a teapot\n")
        if request.POST.get('password','') != handler.password:
            logger_sub.info('Handler {1}{0} permission denied! Password: {2}'.format(
                    handler.name, handler.protocol, request.POST.get('password','')))
            return HttpResponse(status=401, content="permission denied\n")

        handler.active = False if request.POST.get('unregister',False) else True
        handler.save()
        logger_sub.debug('Handler {0} registered successfully'.format(handler.name))
    else:
        logger_sub.info('Handler tried it without HTTPS...')
        return HttpResponse(status=401, content="Unauthorized\n")

    return HttpResponse(status=201)

def write(request):
    if not request.POST or not {'user', 'password', 'ts',
                                    'numbers', 'begin'}.issubset(request.POST):
        logger.info("received an invalid write request: %s" % request)
        return HttpResponse(status=401, content='POST request incomplete!\n')

    if request.POST['user'] not in CLIENT_PASSWORDS.keys() or \
            CLIENT_PASSWORDS[request.POST['user']] != request.POST['password']:
        logger.info("received an unauthorized write request: %s" % request)
        return HttpResponse(status=401, content="permission denied!\n")

    #---------------------- validating input ---------------------

    numbers=[]
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
    try:
        #$foo_$src is mandatory syntax or user-ID, else change here
        src = request.POST['user'].split('_') 
        src = int(src[1]) if len(src)==2 else -1
    except ValueError:
        src = -1

    if src < 0 or not ts or not begin_ts or src not in PA_INDEX.keys() or \
                                len(numbers) > len(PA_INDEX[src]):
        return HttpResponse(status=400, content='did not validate!\n')

    while len(numbers) < len(PA_INDEX[src]):
        numbers.append(-1)
    
    #------------------------- get old number batch --------------------
    num_batch_newest = NewestNumberBatch.objects.filter(src=src)
    if not num_batch_newest.exists():
        num_batches=WaitingNumberBatch.objects.filter(src=src)
        if not num_batches.exists():
            old_num_batch = WaitingNumberBatch(src=src, date=ts, date_delta=0, proc_delay=None)
            old_num_batch.save()
        else:
            old_num_batch = num_batches.latest('date') if num_batches.exists() else None
        num_batch_newest = NewestNumberBatch(src=src, newest=old_num_batch)
    else:
        num_batch_newest=num_batch_newest[0]
    old_num_batch = num_batch_newest.newest

    # Stats --------------------
    # I am very sorry for this. It was a stressfull time, I needed graphs for
    # my masters thesis, quite quickly... But hey, it has a clear syntax!.. :(
    logfile_path = os.path.join(BASE_DIR, 'pa3', 'stats', '{}_{}'.format(datetime.date.today(), src))
    if not os.path.exists(logfile_path):
        open(logfile_path,'w').close()
    logfile = open(logfile_path, 'a')
    # /Stats --------------------

    #------------------------- build new number batch --------------------
    new_batch = None
    for num, _src in zip(numbers, PA_INDEX[src]):
        try:
            old_num_obj = old_num_batch.numbers.get(src=_src) if old_num_batch else 0
        except ObjectDoesNotExist:
            old_num_obj=None
        except MultipleObjectsReturned:
            all_ = old_num_batch.numbers.filter(src=_src)
            old_num_obj = all_[0]
            [i.delete() for i in all_[1:]]
            logger.info('--------------multiples')

        # get todays opening times for validation
        date_ = datetime.datetime.fromtimestamp(ts)
        for i_ in OPENINGS:
            if date_.isoweekday() == i_['weekday']:
                opening_time = i_
                break
        else:
            opening_time = None


        #Save new number
        if (old_num_obj and old_num_obj.number == num) or num == old_num_obj.number:    
            # if number stays or comes outside of the opening times, just update
            num=-1
            #Stats ----------------
            logfile.write('0')
            #/Stats ---------------
        elif num == -1 or not opening_time or 'begin' not in opening_time or \
            opening_time['begin'] > int(date_.strftime('%H%M')) or \
            opening_time['end'] < int(date_.strftime('%H%M'))-60:    #60min Spielraum
            num=-1
            #Stats ----------------
            logfile.write('1')
            #/Stats ---------------
    
        else:
            #Stats ----------------
            logfile.write('1')
            #/Stats ---------------
            if not new_batch:
                new_batch=WaitingNumberBatch()
                new_batch.src_ip = request.META.get('HTTP_X_FORWARDED_FOR','')
                if not new_batch.src_ip:
                    new_batch.src_ip = request.META.get('REMOTE_ADDR','')
                new_batch.src = src
                new_batch.date=ts
                new_batch.date_delta=ts-old_num_batch.date if old_num_batch else -1
                new_batch.proc_delay=None    #Will be set after EVERYTHING else
                new_batch.save()
                new_batch.numbers.add(*list(old_num_batch.numbers.exclude(src=_src)))

            #compute delta, if not first DB-Entry
            dd = ts - old_num_obj.date if old_num_obj else -1
            new_num_obj = WaitingNumber(number=num, src=_src, date=ts, date_delta=dd)
            new_num_obj.save()
            new_batch.numbers.add(new_num_obj)
            proc_delay = time.time()-begin_ts
            new_batch.proc_delay = proc_delay    #Yeah, Time Sync is an issue
            new_batch.save()
            with open('delay.txt','a') as f:
                f.write(str(src)+': '+str(proc_delay)+'\n')

            if dd < (opening_time['end']-opening_time['begin'])*60:
                # Update Stats if num is not first of the day, e.g. date_delta < openings
                try:
                    stat_ = StatisticalData.objects.get(src=_src)
                    stat_.avg_sum += dd
                    stat_.avg_len += 1
                    # sum/len = avg | sum=avg*len | new_avg = sum+dd/len+1
                    stat_.avg = 1.0*stat_.avg_sum/stat_.avg_len
                    stat_.avg_whole = (stat_.avg + stat_.avg_last_two_weeks + stat_.avg_last_same_day) / 3

                    if new_batch.proc_delay > 0:
                        stat_.avg_proc_delay_sum += new_batch.proc_delay
                        stat_.avg_proc_delay_len += 1
                        stat_.avg_proc_delay_whole = 1.0*stat_.avg_proc_delay_sum/stat_.avg_proc_delay_len

                    stat_.date = ts
                    stat_.save()
                except MultipleObjectsReturned:
                    for stats_ in StatisticalData.objects.filter(src=_src):
                        stats_.delete()
                except ObjectDoesNotExist:
                    real_data_begin = int(datetime.date(2013,9,1).strftime("%s"))
                    stat_ = StatisticalData(src=_src, date=ts)
                    stat_qs =WaitingNumber.objects.filter(src=_src).filter(date__gt=real_data_begin).filter(date_delta__lt=60*60*3).filter(date_delta__gt=1)
                    stat_.avg_len = stat_qs.count()
                    stat_.avg_sum = stat_qs.aggregate(s=Sum('date_delta'))['s']
                    stat_.avg = 1.0*stat_.avg_sum/stat_.avg_len
                    stat_.avg_last_two_weeks = stat_.avg 
                    stat_.avg_last_same_day = stat_.avg
                    stat_.avg_whole = (stat_.avg + stat_.avg_last_two_weeks + stat_.avg_last_same_day) / 3

                    stat_.avg_proc_delay_sum = stat_qs.aggregate(s=Sum('proc_delay'))['s']
                    stat_.avg_proc_delay_whole = 1.0*stat_.avg_proc_delay_sum/stat_.avg_len

                    stat_.save()
                    
                except Exception as e:
                    logger.exception('Exception while updating Stats: {}'.format(e))

        #update clients. -1 means no change. Use API for initial values
        payload = { 'action' : 'number',
                    'number' : str(num),
                    'src' : _src,
                    'ts' : str(ts)}
        call_clients(payload)


    #replace NewestNumberBatch
    if new_batch:
        num_batch_newest.newest = new_batch
    num_batch_newest.date = ts
    num_batch_newest.save()

    return HttpResponse(status=201)


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
