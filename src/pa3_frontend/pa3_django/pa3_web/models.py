from django.db import models
from pa3.settings import USER_TO_NAMES
import hashlib

all_displays = []
[all_displays.extend(i.get('displays', [])) for i in USER_TO_NAMES.values()]

class News(models.Model):
    choices_src = [('FR', 'FR'), ('PA','PA')]
    src = models.CharField(max_length=2, choices=choices_src)

    title = models.CharField(max_length=500)
    content = models.TextField()

    date = models.DateTimeField()

    def __unicode__(self):
        return '{}: "{}" - {}'.format(self.src, self.title[:20], self.content[:100])


class Subscriber(models.Model):
    src = models.CharField(choices=zip(all_displays, all_displays), max_length=50)
    protocol = models.CharField(max_length=50)
    identifier = models.CharField(max_length=200)
    number = models.SmallIntegerField()
    buffer = models.SmallIntegerField()

    def __unicode__(self):
        return '{}: number {} at {}'.format(self.identifier, self. number, self.src)

    @staticmethod
    def http_request_to_identifier(request):
        id_string = hashlib.sha256()
        for info in ['HTTP_ACCEPT_LANGUAGE', 'HTTP_USER_AGENT', 'REMOTE_ADDR', 'HTTP_X_FORWARDED_HOST']:
            id_string.update(request.META.get(info, '_').encode('utf-8'))

        return id_string.hexdigest()

    def serialize(self):
        return {'src': self.src, 'number': self.number, 'buffer': self.buffer}

    def _is_due(self, number):
        return number >= self.number - self.buffer

    def handle(self, number):
        if not self._is_due(number):
            return

        if self.protocol == 'browser':
            return
        if self.protocol == 'sms':
            from pa3_web.subscription_sms_handling import notify as notify_sms
            notify_sms(self)
            self.delete()
