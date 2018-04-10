from django import template
from django.utils import timezone
from django.utils.translation import ungettext, ugettext

import datetime, pytz, logging
from pa3.settings import TIME_ZONE

register = template.Library()
logger = logging.getLogger('web')


@register.filter
def timesinceseconds(d, now=None, reversed=False):
    """
    Takes two datetime objects and returns the time between d and now
    as a nicely formatted string, e.g. "10 minutes".  If d occurs after now,
    then "0 minutes" is returned.
	Dates and timestamps get converted to datetime before computation.

    Units used are years, months, weeks, days, hours, minutes and seconds.
    Microseconds are ignored.  Up to two adjacent units will be
    displayed.  For example, "2 weeks, 3 days" and "1 year, 3 months" are
    possible outputs, but "2 weeks, 3 hours" and "1 year, 5 days" are not.

    Adapted from http://blog.natbat.co.uk/archive/2003/Jun/14/time_since
    """
    
    chunks = (
      (60 * 60 * 24 * 365, lambda n: ungettext('year', 'years', n)),
      (60 * 60 * 24 * 30, lambda n: ungettext('month', 'months', n)),
      (60 * 60 * 24 * 7, lambda n: ungettext('week', 'weeks', n)),
      (60 * 60 * 24, lambda n: ungettext('day', 'days', n)),
      (60 * 60, lambda n: ungettext('hour', 'hours', n)),
      (60, lambda n: ungettext('minute', 'minutes', n)),
      (1, lambda n: ungettext('second', 'seconds', n))
    )

    # Convert input dates and timestamps to datetimes
    if not isinstance(d, datetime.datetime):
        if isinstance(d, datetime.date):
            d = timezone.datetime(d.year, d.month, d.day)
        try:
            d = timezone.datetime.fromtimestamp(float(d), tz=pytz.timezone(TIME_ZONE))
        except:
            return ''
    if now and not isinstance(now, datetime.datetime):
        if isinstance(d, datetime.date):
            now = timezone.datetime(now.year, now.month, now.day)
        try:
            now = timezone.datetime.fromtimestamp(float(now), tz=pytz.timezone(TIME_ZONE))
        except ValueError:
            return ''

    if not now:
        now = timezone.now()

    delta = (d - now) if reversed else (now - d)
    # ignore microseconds
    since = delta.days * 24 * 60 * 60 + delta.seconds
    if since <= 0:
        # d is in the future compared to now, stop processing.
        return u'0 ' + ugettext('seconds')
    i, count, seconds, name = 0, -1, 0, lambda f: f
    for i, (seconds, name) in enumerate(chunks):
        count = since // seconds
        if count != 0:
            break
    s = ugettext('%(number)d %(type)s') % {'number': count, 'type': name(count)}
    if i + 1 < len(chunks):
        # Now get the second item
        seconds2, name2 = chunks[i + 1]
        count2 = (since - (seconds * count)) // seconds2
        if count2 != 0:
            s += ugettext(', %(number)d %(type)s') % {'number': count2, 'type': name2(count2)}
    return s

@register.filter
def timeuntilseconds(d, now=None):
    """
    Like timesinceseconds, but returns a string measuring the time
    until the given time.
    """
    return timesinceseconds(d, now, reversed=True)


@register.filter
def timesincesecondsonly(d, now=None):
    """
    Like timesinceseconds, but returns a string measuring the time
    until the given time.
    """
    return timesinceseconds(d, now).split(',')[0]





