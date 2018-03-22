import logging
import datetime, requests, re
from pa3_web.models import News
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned


class NewsChanged(Exception):
    pass


def check_news_validity(news_object):
    now = datetime.datetime.now()
    if now - news_object.last_checked < datetime.timedelta(seconds=12 * 60 * 60):
        return True

    if news_object.src == 'PA':
        resp = requests.get('http://www.pruefungen.tu-berlin.de/menue/aktuell/')
        r = re.search(r'</span></h2><p>Zuletzt aktualisiert:&nbsp;(.*?)<a href=', resp.text)

        date = r.group(1)
        day, month, year = date.split('.')
        date = datetime.date(2000+int(year), int(month), int(day))
        if date > news_object.date:
            raise NewsChanged()
        news_object.last_checked = now
        news_object.save()

    if news_object.src == 'FR':
        req = requests.get('http://wiki.freitagsrunde.org/Vorlage:HauptseiteNewsBox',
                           headers={'If-Modified-Since': news_object.last_checked.ctime()})

        if req.status_code == 304:
            news_object.last_checked = now
            news_object.save()
        elif req.status_code == 200:
            raise NewsChanged()
        else:
            raise IOError()

    return True


def update_news():
    news = {}
    try:
        news['pa_news'] = update_news_pa()
    except IOError:
        news['pa_error'] = 'Pr&uuml;fungsamt-Webseite nicht erreichbar!'
    except Exception as e:
        logging.exception('Exception while checking PA news: {}'.format(e))
        news['pa_error'] = 'Server Error!'

    try:
        news['fr_news'] = update_news_fr()
    except IOError:
        news['fr_error'] = 'Freitagsrunden-Webseite nicht erreichbar!'
    except Exception as e:
        logging.exception('Exception while checking FR news: {}'.format(e))
        news['fr_error'] = 'Server Error!'

    return news


def update_news_pa():
    try:
        pa_news = News.objects.get(src='PA')
        if check_news_validity(pa_news):
            return pa_news
    except (MultipleObjectsReturned, ObjectDoesNotExist, NewsChanged):
        return create_news_pa()


def update_news_fr():
    try:
        fr_news=News.objects.get(src='FR')
        if check_news_validity(fr_news):
            return fr_news
    except (MultipleObjectsReturned, ObjectDoesNotExist, NewsChanged, IOError):
        return create_news_fr()

        
def create_news_pa():
    now = datetime.datetime.now()

    pa_print = requests.get('http://www.pruefungen.tu-berlin.de/menue/aktuell/').text
    begin=pa_print.find('<div id="main">')                #main news content
    begin=pa_print.find('<div id="c', begin)            #first post
    end = pa_print.find('</div>', begin)+len('</div>')    #end of first post
    pa_new_news=pa_print[begin:end]
    pa_new_date = now
    for i in News.objects.filter(src='PA'):
        i.delete()
    pa_new = News(src='PA', date=pa_new_date, news=pa_new_news, last_checked=now)
    pa_new.save()
    return pa_new


def create_news_fr():
    now = datetime.datetime.now()

    fr = requests.get('http://wiki.freitagsrunde.org/Vorlage:HauptseiteNewsBox').text
    begin=fr.find('<div class="content">')        #main news content
    begin=fr.find('<span class="mw-headline"', begin)            #first post
    end = fr.find('<span class="mw-headline"', begin+1)        #end of first post    #FIXME: Fails if only 1 post
    fr_raw=fr[begin:end]
    fr_raw=re.sub(r'class="news-date"', 'style="text-align:right;font-size:0.8em;color:#666;-webkit-column-span:all;-moz-column-span:all;column-span:all"', fr_raw)
    fr_raw=re.sub(r'class="mw-headline"', 'style="margin:0 0.5em 0 0;"', fr_raw)    #convert styles
    fr_raw=re.sub(r'href="/(.*?)"', 'href="http://wiki.freitagsrunde.org/\1"', fr_raw) #absolutify links
    fr_raw=re.sub(r'<span class="editsection">.*?</span>', '', fr_raw)    #remove Bearbeiten

    fr_news=fr_raw
    fr_date_t=re.search(r'<i>.*?, aktualisiert am (.*?)</i>', fr_news)
    if not fr_date_t:
        fr_date_t=re.search(r'<i>News erstellt am (.*?)</i>', fr_news)
    if fr_date_t:
        try:
            fr_date = fr_date_t.group(1)
            fr_news_end = fr_news[:fr_date_t.start()].rfind('<div')
            fr_news = fr_news[:fr_news_end] #deterministic end of article
            day, m_y = fr_date.split('.')
            month, year = m_y.strip().split(' ')
            if '\xc3\xa4' in month:
                month='March'
            month = datetime.datetime.strptime(month[:3].replace('z','c').replace('k','c').replace('i','y'), '%b').month
            fr_date = datetime.date(int(year), month, int(day)).strftime('%s')
        except Exception:
            fr_date=now
    else:
        fr_date = now
    for i in News.objects.filter(src='FR'):
        i.delete()
    fr_new = News(src='FR', date=fr_date, news=fr_news, last_checked=now)
    fr_new.save()
    return fr_news
