# -*- encoding: utf-8 -*-

from django import template
from django.utils.translation import ugettext

import datetime

register = template.Library()


@register.simple_tag
def pa_openings(opening_d=None):
    if opening_d is None:
        opening_d = {}
    if 'weekday' not in opening_d:
        return ''
    weekday = int(opening_d['weekday'])
    opening = {'format1': '', 'format2': '', 'weekday': ugettext(datetime.date(1970, 1, 4+weekday).strftime('%A'))}

    if 'begin' in opening_d and 'end' in opening_d:
        begin = "%.4i" % opening_d['begin']
        end = "%.4i" % opening_d['end']

        opening['openings'] = '%s:%s - %s:%s' % (begin[:2],begin[2:], end[:2],end[2:])
    else:
        opening['openings'] = ugettext('closed')

    now = datetime.datetime.now()
    if now.isoweekday() == weekday:
        opening['format1']=' class="current"'
        opening['format2']=' class="current"'
        if 'begin' in opening_d and 'end' in opening_d:
            now_m = now.hour*60 + now.minute + 30
            begin_m=int(begin[:2])*60+int(begin[2:])
            end_m = int(end[:2])*60+int(end[2:])
            if now_m >= begin_m and now_m <= end_m:
                opening['format2']=' class="current on"'
        
    return '<dt%(format1)s>%(weekday)s</dt><dd%(format2)s>%(openings)s</dd>' % opening
