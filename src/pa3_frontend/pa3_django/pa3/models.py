from django.db import models
from django.utils.translation import ugettext as _
from django.utils import timezone

from pa3.settings import USER_TO_NAMES
from pa3_web.templatetags.pa3_timesinceseconds import timesincesecondsonly, timesinceseconds


all_displays = []
[all_displays.extend(i.get('displays', [])) for i in USER_TO_NAMES.values()]
choices_displays = zip(all_displays, all_displays)

class StatisticalData(models.Model):
    # Stores statistical information on the numbers, to minimize the
    # computation effort
    src = models.CharField(max_length=50, choices=choices_displays)

    date = models.DateTimeField(default=timezone.now)  # for sorting purposes

    avg = models.FloatField(default=0.0)  # current Average
    avg_len = models.IntegerField(default=-1)  # Length over which the avg is computed (count())
    avg_sum = models.IntegerField(default=0)  # Sum from which the avg is computed (avg=sum/len)

    avg_proc_delay_sum = models.IntegerField(default=0)  # Sum from which the avg_proc_delay is computed (avg=sum/len)
    avg_proc_delay_len = models.IntegerField(default=-1)  # Len from which the avg_proc_delay is computed (avg=sum/len)

    avg_last_two_weeks = models.FloatField(default=0.0)  # recomputed every night
    avg_last_same_day = models.FloatField(default=0.0)  # recomputed every night

    avg_whole = models.FloatField(default=0.0)  # current weighted Average
    avg_proc_delay_whole = models.FloatField(default=0.0)  # current Average Processing Delay

    def __unicode__(self):
        return '{self.src}: Avg={self.avg} for {self.avg_len} entries'.format(self=self)

    def serialize(self):
        return {'src': self.src, 'date': self.date.strftime('%s'), 'avg': self.avg,
                'avg_last_two_weeks': self.avg_last_two_weeks,
                'avg_last_same_day': self.avg_last_same_day,
                'avg_whole': self.avg_whole,
                'avg_proc_delay_whole': self.avg_proc_delay_whole}


class WaitingNumber(models.Model):
    src = models.CharField(choices=choices_displays, max_length=50)
    date = models.DateTimeField()
    date_delta = models.IntegerField(null=True)
    proc_delay = models.FloatField(null=True)
    number = models.SmallIntegerField()

    statistic = models.ForeignKey(StatisticalData, on_delete=None)
    
    class Meta:
        ordering = ['-date', 'src']

    def __unicode__(self):
        return '{} | {}: {}'.format(self.number, str(self.date), self.src)

    def serialize(self, verbose=False):
        serialized = {'src': self.src, 'date': self.date.strftime('%s'), 'number': self.number,
                      'proc_delay': self.proc_delay, 'date_delta': self.date_delta,
                      'statistics': self.statistic.serialize()}
        if verbose:
            called_before = (timezone.now() - self.date).seconds
            serialized['called'] = _("called {} before".format(timesinceseconds(self.date))) \
                if called_before < 1880 else "-"
        return serialized


class WaitingNumberBatch(models.Model):
    choices_src = list(zip(USER_TO_NAMES.keys(), [i.get('placement', '?') for i in USER_TO_NAMES.values()]))
    src = models.CharField(choices=choices_src, db_index=True, max_length=50)
    src_ip = models.GenericIPAddressField()

    date = models.DateTimeField(db_index=True, default=timezone.now)
    date_delta = models.IntegerField(null=True)
    proc_delay = models.FloatField(null=True)
    numbers = models.ManyToManyField(WaitingNumber)

    class Meta:
        ordering = ['-date', 'src']

    def __unicode__(self):
        return '{} | {}'.format(self.src, str(self.date))

    def serialize_numbers(self, verbose=False):
        return [num.serialize(verbose) for num in self.numbers.all()]

    def serialize(self, verbose=False):
        return {'src': self.src, 'date': self.date.strftime('%s'), 'src_ip': self.src_ip,
                'numbers': [num.serialize(verbose) for num in self.numbers.all()],
                'proc_delay': self.proc_delay, 'date_delta': self.date_delta,
                'placement': USER_TO_NAMES.get(self.src, {}).get('placement')}


class NewestNumberBatch(models.Model):
    # To minimze database queries, the newest Batch gets stored seperately and 
    # only contains the newest WaitingNumberBatch
    choices_src = list(zip(USER_TO_NAMES.keys(), [i.get('placement', '?') for i in USER_TO_NAMES.values()]))
    src = models.CharField(choices=choices_src, max_length=50)
    date = models.DateTimeField()
    newest = models.ForeignKey(WaitingNumberBatch, on_delete=None)

    def __unicode__(self):
        return '{} | {}'.format(self.src, str(self.newest))

    def serialize(self, verbose=False):
        serialized = {'newest': self.newest.serialize(verbose), 'date': self.date.strftime('%s')}
        if verbose:
            updated = (timezone.now() - self.date).seconds
            serialized['updated'] = "" if updated < 10 else _(
                "Warning! Last check {} ago".format(timesincesecondsonly(self.date)))
        return serialized
