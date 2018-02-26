from django.db import models
from pa3.settings import PA_INDEX


class WaitingNumber(models.Model):
    choices_src = zip(PA_INDEX.values(), PA_INDEX.values())
    src = models.CharField(max_length=14, choices=choices_src)
    date = models.IntegerField()
    date_delta = models.IntegerField(null=True)
    number = models.SmallIntegerField()
    
    class Meta:
        ordering = ['-date', 'src']

    def __unicode__(self):
        return '{} | {}: {}'.format(self.number, str(self.date), self.src)


class WaitingNumberBatch(models.Model):
    choices_src = zip(PA_INDEX.keys(), ['H%s: %s' % (k,', '.join(v)) for k,v in PA_INDEX.items()])
    src = models.IntegerField(choices=choices_src, db_index=True)
    src_ip = models.GenericIPAddressField()

    date = models.IntegerField(db_index=True)
    date_delta = models.IntegerField(null=True)
    proc_delay = models.FloatField(null=True)
    numbers = models.ManyToManyField(WaitingNumber)

    class Meta:
        ordering = ['-date', 'src']

    def __unicode__(self):
        return str(self.src)+' | '+str(self.date)


class NewestNumberBatch(models.Model):
    # To minimze database queries, the newest Batch gets stored seperately and 
    # only contains the newest WaitingNumberBatch
    choices_src = zip(PA_INDEX.keys(), ['H%s: %s' % (k,', '.join(v)) for k,v in PA_INDEX.items()])
    src = models.IntegerField(choices=choices_src)
    date = models.IntegerField()
    newest = models.ForeignKey(WaitingNumberBatch, on_delete=None)

    def __unicode__(self):
        return str(self.src)+' | '+str(self.newest)


class StatisticalData(models.Model):
    # Stores statistical information on the numbers, to minimize the 
    # computation effort
    choices_src = zip(PA_INDEX.values(), PA_INDEX.values())
    src = models.CharField(max_length=14, choices=choices_src)

    date = models.IntegerField()    #for sorting purposes

    avg = models.FloatField()        #current Average
    avg_len = models.IntegerField()    #Length over which the avg is computed (count())
    avg_sum = models.IntegerField()    #Sum from which the avg is computed (avg=sum/len)

    avg_proc_delay_sum = models.IntegerField()    #Sum from which the avg_proc_delay is computed (avg=sum/len)
    avg_proc_delay_len = models.IntegerField()    #Len from which the avg_proc_delay is computed (avg=sum/len)

    avg_last_two_weeks = models.FloatField()    #recomputed every night
    avg_last_same_day = models.FloatField()        #recomputed every night
    
    avg_whole = models.FloatField()        #current weighted Average
    avg_proc_delay_whole = models.FloatField()        #current Average Processing Delay

    def __unicode__(self):
        return '{self.src}: Avg={self.avg} for {self.avg_len} entries'.format(self=self)


class ClientHandler(models.Model):
    #A ClientHandler handles the subscriptions and updates to its clients 
    #for its protocol. Communication is started through the webinterface or 
    #the Client itself, but is continued only between the ClientHandler and 
    #the Client. Each ClientHandler has to register to the server to get 
    #updates, and subscriptions through the webinterface.
    #
    #The ClientHandler and the server speak HTTP.
    name = models.CharField(max_length=100)        #description (kais jabberbot)
    protocol = models.CharField(max_length=20)    #protocol (mail, xmpp, ...)
    address = models.CharField(max_length=500)    #HTTP-url
    password = models.CharField(max_length=100)    #pw for the server to validate
    active = models.BooleanField()    #flag to see which handlers are operational

    def __unicode__(self):
        return '%s - %s-Handler @ %s' % (self.name, self.protocol, self.address)
