# -*- coding: utf-8 -*-

import os
import copy
import _md5
import json

from django.utils import timezone
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.http import HttpResponse, JsonResponse
from django.utils.translation import ugettext as _

import logging

from pa3.models import WaitingNumberBatch, NewestNumberBatch, StatisticalData
from pa3.settings import USER_TO_NAMES, OPENINGS, DATABASES, BASE_DIR

from pa3_web import news_handling

logger = logging.getLogger('web')
logger_req = logging.getLogger('django.request')


def get_current_numbers_request(request):
    return JsonResponse(get_current_numbers(), safe=False)


def get_current_numbers(src=None):
    sources = [src] if src in USER_TO_NAMES.keys() else USER_TO_NAMES.keys()
    data = []
    for k in sources:
        try:
            newest = NewestNumberBatch.objects.get(src=k)
            data.append(newest.serialize(verbose=True))
        except ObjectDoesNotExist:
            logging.warning('Warning! Database for the Display above Room {} is empty!'.format(k))

    return data


def index(request, src=None):
    dict_ = dict()
    dict_['data'] = get_current_numbers(src)
    dict_['openings'] = OPENINGS

    if src is None:
        dict_['news'] = news_handling.update_news()

    return render_to_response('index.html', dict_, RequestContext(request))


def update_dump(request):
    stats_root = os.path.join(BASE_DIR, 'pa3', 'stats/')

    # Remove old dump(s)
    try:
        [os.remove(os.path.join(stats_root, i)) for i in os.listdir(stats_root) if i.endswith('.gz')]
    except Exception as e:
        logger.fatal('Could not remove old dump, was: {0}'.format(e))

    # Create new dump
    database = DATABASES['default']
    now = timezone.now().strftime('%s')
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

    pa_rooms = [paT] if paT else USER_TO_NAMES.keys()
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
                  'validFrom': timezone.datetime(1970, 1, 1).ctime(),
                  'validThrough': timezone.datetime(2030, 1, 1).ctime(),
                  'dayOfWeek': timezone.datetime(1970, 1, 4 + op['weekday']).strftime('%A')}
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
                      'approxwaittime': (timezone.now() + timezone.timedelta(0, int(avg))).ctime(),
                      'date': src_counter.date.ctime(),
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


def api(request, pa=None):
    src = [pa] if pa else USER_TO_NAMES.keys()
    result = {'entries': [], 'errors': [], 'openings': OPENINGS}

    for s in src:
        try:
            newest = NewestNumberBatch.objects.get(src=s)
            result['entries'].append(newest.newest.serialize())
        except (MultipleObjectsReturned, ObjectDoesNotExist):
            result['errors'].append("Pruefungsamt '{}' not found!".format(s))

    return HttpResponse(json.dumps(result), content_type='application/json; charset=utf8')


def check_notify(request):
    down = []
    for k in USER_TO_NAMES.keys():
        try:
            newest = NewestNumberBatch.objects.get(src=k)
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            continue
        offline_m = (timezone.now() - newest.date).seconds / 60
        if offline_m > 5:
            status = '{0} down for {1} minutes'.format(k, int(offline_m))
            down.append(status)
            if (offline_m < 60 or not offline_m % 10) and offline_m < 600:
                logger_req.fatal(status)
    return HttpResponse(status=200, content='Everything\'s fine' if not down else '\n'.join(down))
