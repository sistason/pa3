# -*- coding: utf-8 -*-

import datetime, os, re
import copy	#for the usual cases of deepcopy...
import _md5
import json

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.http import HttpResponse

import logging

from pa3_web.forms import SubscribeForm, BlacklistForm
from pa3.models import WaitingNumberBatch, NewestNumberBatch, ClientHandler, StatisticalData
from pa3.settings import PA_INDEX, OPENINGS, DATABASES, BASE_DIR

from pa3_web import news_handling

logger = logging.getLogger('web')
logger_req = logging.getLogger('django.request')


def index(request, src=None, subscribeform=None):
    errors, data = [], []
    now_ts = int(datetime.datetime.now().strftime('%s'))
    dict_ = {'data': data, 'errors': errors, 'PA_frame': None, 'FR_frame': None, 'subscribeforms': []}

    if src == "-1":
        dict_['dbg'] = True
        src = None
    else:
        dict_['single'] = True if src else False
    dict_['null'] = datetime.datetime.fromtimestamp(0)

    if src:
        if int(src) in PA_INDEX.keys():
            srces = [src]
            if src == '13':
                dict_['dbg'] = True
        else:
            for paT, pas in PA_INDEX.items():
                if re.search(src, ' '.join(pas)):
                    srces = [paT]
                    break
            else:
                srces = [2, 10, 23]
                src = None
    else:
        srces = [2, 10, 23]

    for k in srces:
        try:
            newest = NewestNumberBatch.objects.get(src=k)
            num = newest.newest  # get newest WaitingNumberBatch via newest-table
        except ObjectDoesNotExist:
            try:
                newest = num = WaitingNumberBatch.objects.filter(src=k).latest('date')
            except ObjectDoesNotExist:
                errors.append('Warning! Database for the Display above Room H{:02} is empty!'.format(k))
                continue
        except MultipleObjectsReturned:
            newest = num = WaitingNumberBatch.objects.filter(src=k).latest('date')

        numbers = num.numbers.all()
        updated = newest.date if now_ts - newest.date > 10 else 0
        nums = {'prev': updated, 'src': num.src, 'numbers': []}
        for i in numbers:
            date_long = i.date if now_ts - i.date < 60 * 30 else 0
            try:
                avg_ = StatisticalData.objects.get(src=i.src).avg_whole
            except (MultipleObjectsReturned, ObjectDoesNotExist):
                avg_ = 0
            nums['numbers'].append({'pa': i.src, 'nr': i.number, 'prev': date_long, 'avg': avg_})
        nums['numbers'].sort(key=lambda a: int(re.search(r'(\d+)/?', a['pa']).group(1)))

        data.append(nums)

    if not src:
        dict_ = news_handling.update_news(dict_)
        dict_['openings'] = OPENINGS

    # for cli_handler in ClientHandler.objects.filter(active=True):
    #     dict_['subscribeforms'].append(SubscribeForm(
    #         cli_handler.protocol))
    # if subscribeform:
    #     try:
    #         [dict_['subscribeforms'].remove(i) for i in dict_['subscribeforms']
    #          if i.protocol == subscribeform.protocol]
    #     except:
    #         pass
    #     dict_['subscribeforms'].insert(0, subscribeform)

    return render_to_response('index.html', dict_, RequestContext(request))


def abuse(request, blacklistform=None):
    dict_ = {}
    dict_['blacklist_form'] = blacklistform if blacklistform else BlacklistForm()

    return render_to_response('abuse.html', dict_, RequestContext(request))


def update_dump(request):
    stats_root = os.path.join(BASE_DIR, 'pa3', 'stats/')

    # Remove old dump(s)
    try:
        [os.remove(os.path.join(stats_root, i)) for i in os.listdir(stats_root) if i.endswith('.gz')]
    except Exception as e:
        logger.fatal('Could not remove old dump, was: {0}'.format(e))

    # Create new dump
    database = DATABASES['default']
    now = datetime.date.today().strftime('%s')
    dump_location = os.path.join(stats_root, 'dump_{0}.gz'.format(now))

    cmdline = 'mysqldump --user={0} --password={1} {2} web_waitingnumber | gzip > {3}'
    cmdline = cmdline.format(database['USER'], database['PASSWORD'], database['NAME'], dump_location)
    del DATABASES

    try:
        os.system(cmdline)
    except Exception as e:
        del cmdline
        logger.fatal('Could not dump, was: {0}'.format(e))
        return HttpResponse(status=400, content='Dump not created!')

    del cmdline
    return HttpResponse(status=200, content='Dump created')


def api2(request, paT=None, ops=None, pa=None):
    entries = []

    pa_rooms = [paT] if paT else PA_INDEX.keys()
    for pa_room in pa_rooms:
        try:
            newest = NewestNumberBatch.objects.get(src=pa_room)  # get newest WaitingNumberBatch via newest-table
        except (MultipleObjectsReturned, ObjectDoesNotExist):
            #			dict['errors'].append("Table '%s' not found!" % pa_room)
            continue
        num = newest.newest
        nums = num.numbers.all()

        nums = nums.filter(src='H ' + pa) if pa else nums
        if not nums:
            #			dict['errors'].append("Pruefungsamt '%s' not found!" % pa)
            continue

        ticket_place = {
            "type": "Place",
            "uid": _md5.md5(str(pa_room)).hexdigest(),
            "subType": "Prüfungsamt",
            "name": pa_room,
            "alternateName": [
                "H {0}".format(pa_room)
            ],
            "url": "http://www.pruefungen.tu-berlin.de/",
            "description": "Prüfungsamt der TU Berlin, Raum {0}".format(pa_room),
            "image": "http://www.tu-berlin.de/fileadmin/Aperto_design/img/logo_01.gif",
            "video": "https://www.youtube.com/watch?v=BROWqjuTM0g",
            "address": {
                "addressCountry": "Germany",
                "addressLocality": "Berlin",
                "addressRegion": "Berlin",
                "postOfficeBoxNumber": "",
                "postalCode": "10623",
                "streetAddress": "Straße des 17. Juni 135"
            },
            "openingHours":
                [{'opens': ':'.join([str(op['begin'])[:-2], str(op['begin'])[-2:]]),
                  'closes': ':'.join([str(op['end'])[:-2], str(op['end'])[-2:]]),
                  'validFrom': datetime.datetime(1970, 1, 1).ctime(),
                  'validThrough': datetime.datetime(2030, 1, 1).ctime(),
                  'dayOfWeek': datetime.datetime(1970, 1, 4 + op['weekday']).strftime('%A')}
                 for op in OPENINGS if op.has_key('begin')],
            "geo": {
                "type": "GeoShape",
                "uid": "74398574398768945874",
                "polygon": [
                    "12.323590,53.518139,0.000000",
                    "13.324133,53.518108,1.000000",
                    "14.323690,-53.518250,2.000000",
                    "15.323590,-53.518139,3.000000"
                ]
            }
        }

        for src_counter in nums:
            try:
                avg = StatisticalData.objects.get(src=src_counter.src).avg_whole
            except (MultipleObjectsReturned, ObjectDoesNotExist):
                #				dict['errors'].append("Statistical Data for {0} not availible!".format(src_counter.src))
                avg = 0

            ticket = {'type': "Ticket",
                      'uid': _md5.md5(str(src_counter.pk)).hexdigest(),
                      'currentTicketNumber': src_counter.number,
                      'approxwaittime': (datetime.datetime.now() + datetime.timedelta(0, int(avg))).ctime(),
                      'date': datetime.datetime.fromtimestamp(src_counter.date).ctime(),
                      'room': src_counter.src,
                      'servicetype': {"name": "Prüfungsamt"},
                      'counter': src_counter.pk,
                      }
            ticket_place_copy = copy.deepcopy(ticket_place)
            ticket['place'] = ticket_place_copy

            entries.append(ticket)

    resp = HttpResponse(json.dumps(entries), content_type='application/json; charset=utf8')
    resp['Access-Control-Allow-Origin'] = '*'
    return resp


def api(request, paT=None, ops=None, pa=None):
    src = [paT] if paT else PA_INDEX.keys()
    dict = {'entries': [], 'errors': [], 'openings': OPENINGS}
    try:
        if ops and pa:
            if pa and pa.isdigit() and int(pa) < len(OPENINGS):
                dict['openings'] = OPENINGS[int(pa)]
            elif len(pa) > 3:
                translate_dict = {'mo': 0, 'di': 1, 'mi': 2, 'do': 3, 'fr': 4, 'tu': 1, 'we': 2, 'th': 3}
                dict['openings'] = OPENINGS[translate_dict[pa[:2].lower()]]
    except:
        dict['errors'].append('Dayformat for openings not understood')

    if ops:
        return HttpResponse(json.dumps(dict), content_type='application/json; charset=utf8')

    for s in src:
        try:
            newest = NewestNumberBatch.objects.get(src=s)  # get newest WaitingNumberBatch via newest-table
        except (MultipleObjectsReturned, ObjectDoesNotExist):
            dict['errors'].append("Table '%s' not found!" % s)
            continue
        num = newest.newest
        nums = num.numbers.all()

        nums = nums.filter(src='H ' + pa) if pa else nums
        if not nums:
            dict['errors'].append("Pruefungsamt '%s' not found!" % pa)
            continue
        current = {'date': newest.date, 'src': s}
        n = []
        for i in nums:
            try:
                avg = StatisticalData.objects.get(src=i.src).avg_whole
            except (MultipleObjectsReturned, ObjectDoesNotExist):
                dict['errors'].append("Statistical Data for {0} not availible!".format(i.src))
                avg = 0
            n.append({'src': i.src.split(' ')[1], 'date': i.date, 'num': i.number, 'avg': avg})
        current['numbers'] = n

        dict['entries'].append(current)

    return HttpResponse(json.dumps(dict), content_type='application/json; charset=utf8')


def check_notify(request):
    down = []
    for k in [2, 10, 23, 13]:
        try:
            newest = NewestNumberBatch.objects.get(src=k)
        except:
            continue
        offline_m = (int(datetime.datetime.now().strftime('%s')) - newest.date) / 60
        if offline_m > 5:
            status = 'H{0} down for {1} minutes'.format(k, offline_m)
            down.append(status)
            if (offline_m < 60 or not offline_m % 10) and offline_m < 600:
                logger_req.fatal(status)
    return HttpResponse(status=200, content='Everything\'s fine' if not down else '\n'.join(down))
