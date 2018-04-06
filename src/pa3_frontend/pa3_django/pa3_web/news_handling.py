import logging
logger = logging.getLogger(__name__)
import requests, re, bs4

from django.utils import timezone
from django.http import HttpResponse

from pa3_web.models import News


def update_news():
    news = {}
    try:
        pa_newest = News.objects.filter(src='PA')
        if pa_newest.exists():
            news['pa_news'] = pa_newest.latest('date')
        else:
            news['pa_error'] = 'Pr&uuml;fungsamt-Webseite nicht verf&uuml;gbar'
    except (IOError, requests.exceptions.Timeout):
        news['pa_error'] = 'Pr&uuml;fungsamt-Webseite nicht erreichbar!'
    except Exception as e:
        logger.exception('Exception while checking PA news: {}'.format(e))
        news['pa_error'] = 'Server Error!'

    try:
        fr_newest = News.objects.filter(src='FR')
        if fr_newest.exists():
            news['fr_news'] = fr_newest.latest('date')
        else:
            news['fr_error'] = 'Freitagsrunden-Webseite nicht verf&uuml;gbar'
    except (IOError, requests.exceptions.Timeout):
        news['fr_error'] = 'Freitagsrunden-Webseite nicht erreichbar!'
    except Exception as e:
        logger.exception('Exception while checking FR news: {}'.format(e))
        news['fr_error'] = 'Server Error!'

    return news


def check_news(request):
    check_news_fr()
    check_news_pa()
    return HttpResponse(status=200)


def check_news_pa():
    now = timezone.now()
    newest = News.objects.filter(src='PA')

    pa_print = requests.get('https://www.pruefungen.tu-berlin.de/menue/home/', timeout=5).content
    soup = bs4.BeautifulSoup(pa_print, 'lxml')
    first_news = soup.find('div', attrs={'class': 'accordionelement'})
    title = first_news.h1.text
    if newest.exists():
        if newest.latest('date').title == title:
            return
    content = first_news.find('div', attrs={'class': 'csc-text'})

    pa_new = News(src='PA', date=now, content=content.prettify(formatter="html"), title=title, last_checked=now)
    pa_new.save()


def check_news_fr():
    now = timezone.now()
    newest = News.objects.filter(src='FR')

    host = 'https://wiki.freitagsrunde.org'
    fr_print = requests.get('https://wiki.freitagsrunde.org/Vorlage:HauptseiteNewsBox', timeout=5).content
    soup = bs4.BeautifulSoup(fr_print, 'lxml')
    content_ = soup.find('div', attrs={'class': 'mw-content-ltr'}).next_element
    title = content_.text.strip()
    if newest.exists():
        if newest.latest('date').title == title:
            return

    content = []
    iterator = content_.findNextSibling()
    while iterator.findNextSibling().name != 'h3':
        content.append(iterator.prettify(formatter='html'))
        iterator = iterator.findNextSibling()
        if len(content) > 100:
            logger.exception('News from Freitagsrunde was malformed!')
            break

    content_str = ''.join(content)
    content_str = re.sub(r'class="news-date"', 'style="text-align:right;font-size:0.8em;color:#666;'+
                                          '-webkit-column-span:all;-moz-column-span:all;column-span:all"', content_str)
    content_str = re.sub(r'class="mw-headline"', 'style="margin:0 0.5em 0 0;"', content_str)    #convert styles
    content_str = re.sub(r'href="/(.*?)"', r'href="{}/\1"'.format(host), content_str) #absolutify links
    content_str = re.sub(r'<span class="editsection">.*?</span>', '', content_str)    #remove Bearbeiten

    fr_news = News(src='FR', date=now, title=title, content=content_str, last_checked=now)
    fr_news.save()
