from django.db import models


class News(models.Model):
    choices_src=zip(('FR', 'PA'), ('FR','PA'))
    src = models.CharField(max_length=2, choices=choices_src)

    date = models.IntegerField()
    news = models.TextField()
    last_checked = models.IntegerField()

    def __unicode__(self):
        return '%s from %d: %s' % (self.src, self.date, self.news[50:])
