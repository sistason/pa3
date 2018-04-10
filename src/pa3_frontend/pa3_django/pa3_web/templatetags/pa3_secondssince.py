from django import template
from django.utils import timezone
from django.utils.translation import ungettext, ugettext

import datetime, pytz
from pa3.settings import TIME_ZONE

register = template.Library()


@register.filter
def secondssince(d, now=None, reversed=False):

    # Convert input dates and timestamps to datetimes
    if not isinstance(d, datetime.datetime):
        if isinstance(d, datetime.date):
            d = timezone.datetime(d.year, d.month, d.day)
        try:
            d = timezone.datetime.fromtimestamp(float(d), tz=pytz.timezone(TIME_ZONE))
        except Exception:
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

    return 0 if since <= 0 else since

@register.filter
def secondsuntil(d, now=None):
    """
    Like secondssince, but returns a int measuring the time
    until the given time.
    """
    return secondssince(d, now, reversed=True)


