from django.db import models
from pa3.settings import USER_TO_NAMES


class WaitingNumber(models.Model):
    choices_src = zip(USER_TO_NAMES.values(), USER_TO_NAMES.values())
    src = models.CharField(choices=choices_src, max_length=50)
    date = models.IntegerField()
    date_delta = models.IntegerField(null=True)
    proc_delay = models.FloatField(null=True)
    number = models.SmallIntegerField()
    
    class Meta:
        ordering = ['-date', 'src']

    def __unicode__(self):
        return '{} | {}: {}'.format(self.number, str(self.date), self.src)


class WaitingNumberBatch(models.Model):
    choices_src = zip(USER_TO_NAMES.keys(), ['H%s: %s' % (k,', '.join(v)) for k,v in USER_TO_NAMES.items()])
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


class NewestNumberBatch(models.Model):
    # To minimze database queries, the newest Batch gets stored seperately and 
    # only contains the newest WaitingNumberBatch
    choices_src = zip(USER_TO_NAMES.keys(), ['H%s: %s' % (k,', '.join(v)) for k,v in USER_TO_NAMES.items()])
    src = models.CharField(choices=choices_src, max_length=50)
    date = models.IntegerField()
    newest = models.ForeignKey(WaitingNumberBatch, on_delete=None)

    def __unicode__(self):
        return '{} | {}'.format(self.src, str(self.newest))


class StatisticalData(models.Model):
    # Stores statistical information on the numbers, to minimize the 
    # computation effort
    choices_src = zip(USER_TO_NAMES.values(), USER_TO_NAMES.values())
    src = models.CharField(max_length=50, choices=choices_src)

    date = models.IntegerField()    #for sorting purposes

    avg = models.FloatField()        #current Average
    avg_len = models.IntegerField()    #Length over which the avg is computed (count())
    avg_sum = models.IntegerField()    #Sum from which the avg is computed (avg=sum/len)

    avg_proc_delay_sum = models.IntegerField(null=True)    #Sum from which the avg_proc_delay is computed (avg=sum/len)
    avg_proc_delay_len = models.IntegerField(null=True)    #Len from which the avg_proc_delay is computed (avg=sum/len)

    avg_last_two_weeks = models.FloatField()    #recomputed every night
    avg_last_same_day = models.FloatField()        #recomputed every night
    
    avg_whole = models.FloatField()        #current weighted Average
    avg_proc_delay_whole = models.FloatField()        #current Average Processing Delay

    def __unicode__(self):
        return '{self.src}: Avg={self.avg} for {self.avg_len} entries'.format(self=self)
