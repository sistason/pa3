from django.db import models
from pa3.settings import USER_TO_NAMES
import _sha512


class News(models.Model):
    choices_src=zip(('FR', 'PA'), ('FR','PA'))
    src = models.CharField(max_length=2, choices=choices_src)

    title = models.CharField(max_length=500)
    content = models.TextField()

    date = models.DateTimeField()

    def __unicode__(self):
        return '{}: "{}" - {}'.format(self.src, self.title[:20], self.content[:100])


class Subscriber(models.Model):
    displays = [i.get('displays', []) for i in USER_TO_NAMES.values()]
    choices_src = zip(displays, displays)
    src = models.CharField(choices=choices_src, max_length=50)
    identifier = models.CharField(max_length=200)
    number = models.SmallIntegerField()
    buffer = models.SmallIntegerField()

    def __unicode__(self):
        return '{}: number {} at {}'.format(self.identifier, self. number, self.src)

    @staticmethod
    def request_to_identifier(request):
        return _sha512.sha512('foo')

    def serialize(self):
        return {'src': self.src, 'number': self.number, 'buffer': self.buffer}
