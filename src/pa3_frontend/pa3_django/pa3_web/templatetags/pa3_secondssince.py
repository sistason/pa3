from django import template
from django.utils.timezone import is_aware, utc
from django.utils.translation import ungettext, ugettext

import datetime

register = template.Library()


@register.filter
def secondssince(d, now=None, reversed=False):

    # Convert input dates and timestamps to datetimes
    if not isinstance(d, datetime.datetime):
        if isinstance(d, datetime.date):
            d = datetime.datetime(d.year, d.month, d.day)
        try:
            d = datetime.datetime.fromtimestamp(float(d))
        except:
            return ''
    if now and not isinstance(now, datetime.datetime):
        if isinstance(d, datetime.date):
            now = datetime.datetime(now.year, now.month, now.day)
        try:
            now = datetime.datetime.fromtimestamp(float(now))
        except ValueError:
            return ''

    if not now:
        now = datetime.datetime.now(utc if is_aware(d) else None)

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


