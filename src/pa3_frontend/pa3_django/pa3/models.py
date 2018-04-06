from django.db import models
from pa3.settings import USER_TO_NAMES


class StatisticalData(models.Model):
    # Stores statistical information on the numbers, to minimize the
    # computation effort
    displays = [i.get('displays', []) for i in USER_TO_NAMES.values()]
    choices_src = zip(displays, displays)
    src = models.CharField(max_length=50, choices=choices_src)

    date = models.IntegerField()  # for sorting purposes

    avg = models.FloatField()  # current Average
    avg_len = models.IntegerField()  # Length over which the avg is computed (count())
    avg_sum = models.IntegerField()  # Sum from which the avg is computed (avg=sum/len)

    avg_proc_delay_sum = models.IntegerField(null=True)  # Sum from which the avg_proc_delay is computed (avg=sum/len)
    avg_proc_delay_len = models.IntegerField(null=True)  # Len from which the avg_proc_delay is computed (avg=sum/len)

    avg_last_two_weeks = models.FloatField()  # recomputed every night
    avg_last_same_day = models.FloatField()  # recomputed every night

    avg_whole = models.FloatField()  # current weighted Average
    avg_proc_delay_whole = models.FloatField()  # current Average Processing Delay

    def __unicode__(self):
        return '{self.src}: Avg={self.avg} for {self.avg_len} entries'.format(self=self)

    def serialize(self):
        return {'src': self.src, 'date': self.date, 'avg': self.avg,
                'avg_last_two_weeks': self.avg_last_two_weeks,
                'avg_last_same_day': self.avg_last_same_day,
                'avg_whole': self.avg_whole,
                'avg_proc_delay_whole': self.avg_proc_delay_whole}


class WaitingNumber(models.Model):
    displays = [i.get('displays', []) for i in USER_TO_NAMES.values()]
    choices_src = zip(displays, displays)
    src = models.CharField(choices=choices_src, max_length=50)
    date = models.IntegerField()
    date_delta = models.IntegerField(null=True)
    proc_delay = models.FloatField(null=True)
    number = models.SmallIntegerField()

    statistic = models.ForeignKey(StatisticalData, on_delete=None)
    
    class Meta:
        ordering = ['-date', 'src']

    def __unicode__(self):
        return '{} | {}: {}'.format(self.number, str(self.date), self.src)

    def serialize(self):
        return {'src': self.src, 'date': self.date, 'num': self.number,
                'proc_delay': self.proc_delay, 'date_delta': self.date_delta,
                'statistics': self.statistic    .serialize()}


class WaitingNumberBatch(models.Model):
    choices_src = zip(USER_TO_NAMES.keys(), [i.get('placement', '?') for i in USER_TO_NAMES.values()])
    src = models.CharField(choices=choices_src, db_index=True, max_length=50)
    src_ip = models.GenericIPAddressField()

    date = models.IntegerField(db_index=True)
    date_delta = models.IntegerField(null=True)
    proc_delay = models.FloatField(null=True)
    numbers = models.ManyToManyField(WaitingNumber)

    class Meta:
        ordering = ['-date', 'src']

    def __unicode__(self):
        return '{} | {}'.format(self.src, str(self.date))

    def serialize(self):
        return {'src': self.src, 'date': self.date, 'src_ip': self.src_ip,
                'numbers': [num.serialize() for num in self.numbers.all()],
                'proc_delay': self.proc_delay, 'date_delta': self.date_delta}


class NewestNumberBatch(models.Model):
    # To minimze database queries, the newest Batch gets stored seperately and 
    # only contains the newest WaitingNumberBatch
    choices_src = zip(USER_TO_NAMES.keys(), [i.get('placement', '?') for i in USER_TO_NAMES.values()])
    src = models.CharField(choices=choices_src, max_length=50)
    date = models.IntegerField()
    newest = models.ForeignKey(WaitingNumberBatch, on_delete=None)

    def __unicode__(self):
        return '{} | {}'.format(self.src, str(self.newest))

    def serialize(self):
        return {'src': self.src, 'date': self.date,
                'newest': self.newest.serialize()}
