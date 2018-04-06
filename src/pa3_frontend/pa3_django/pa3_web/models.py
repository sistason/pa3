from django.db import models


class News(models.Model):
    choices_src=zip(('FR', 'PA'), ('FR','PA'))
    src = models.CharField(max_length=2, choices=choices_src)

    title = models.CharField(max_length=500)
    content = models.TextField()

    date = models.DateTimeField()

    def __unicode__(self):
        return '{}: "{}" - {}'.format(self.src, self.title[:20], self.content[:100])
