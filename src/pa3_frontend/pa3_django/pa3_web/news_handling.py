import datetime, requests, re
from pa3_web.models import News
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned


def update_news(dict_):
    pa_news, fr_news = None, None
    try:
        pa_news=News.objects.get(src='PA')
    except (MultipleObjectsReturned, ObjectDoesNotExist):
        dict_ = renew_news(dict_, 'PA')

    try:
        fr_news=News.objects.get(src='FR')
    except (MultipleObjectsReturned, ObjectDoesNotExist):
        dict_ = renew_news(dict_, 'FR')

    now=int(datetime.datetime.now().strftime('%s'))
    if pa_news:
        if now-pa_news.last_checked > 12*60*60:
            pa_news.last_checked = now
            pa_news.save()
            try:
                resp=requests.get('http://www.pruefungen.tu-berlin.de/menue/aktuell/')
                r = re.search(r'</span></h2><p>Zuletzt aktualisiert:&nbsp;(.*?)<a href=', resp.text)
                try:
                    date = r.group(1)
                    day, month, year = date.split('.')
                    date = datetime.date(2000+int(year), int(month), int(day))
                    if int(date.strftime('%s')) > pa_news.date:
                        raise Exception()
                    dict_['PA_frame']=pa_news.news
                except Exception:
                    renew_news(dict_, 'PA', resp.text)

            except IOError as e:
                dict_['PA_frame']='Pr&uuml;fungsamt-Webseite nicht erreichbar! %s' % str(e)
        else:
            dict_['PA_frame']=pa_news
            dict_['PA_frame_date']=datetime.datetime.fromtimestamp(pa_news.date)

    if fr_news:
        if now-fr_news.last_checked > 12*60*60:
            req = requests.get('http://wiki.freitagsrunde.org/Vorlage:HauptseiteNewsBox',
                             headers={'If-Modified-Since':
                                          datetime.datetime.fromtimestamp(fr_news.last_checked).ctime()})
            fr_news.last_checked = now
            fr_news.save()

            # FIXME: richtigrum so?
            if req.status_code == 304:
                dict_['FR_frame']=fr_news.news
            elif req.status_code == 200:
                renew_news(dict_, 'FR', req.text)
            else:
                dict_['FR_frame']='Freitagsrunden-Webseite nicht erreichbar! %s' % str(e)
        else:
            dict_['FR_frame']=fr_news
            dict_['FR_frame_date']=datetime.datetime.fromtimestamp(fr_news.date)
    return dict_

        
def renew_news(dict_, src, data=None):
    now=int(datetime.datetime.now().strftime('%s'))
    if src == 'PA':
        try:
            pa_print = data if data else requests.get('http://www.pruefungen.tu-berlin.de/menue/aktuell/').text
            begin=pa_print.find('<div id="main">')                #main news content
            begin=pa_print.find('<div id="c', begin)            #first post
            end = pa_print.find('</div>', begin)+len('</div>')    #end of first post
            pa_new_news=pa_print[begin:end]
            pa_new_date = now
            for i in News.objects.filter(src='PA'):
                i.delete()
            pa_new=News(src='PA', date=pa_new_date, news=pa_new_news, last_checked=now)
            pa_new.save()
            dict_['PA_frame']=pa_new_news
        except Exception as e:
            dict_['PA_frame']='Pr&uuml;fungsamt-Webseite nicht erreichbar! %s' % str(e)

    elif src == 'FR':
        try:
            fr= data.read() if data else requests.get('http://wiki.freitagsrunde.org/Vorlage:HauptseiteNewsBox').text
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
                    month=datetime.datetime.strptime(month[:3].replace('z','c').replace('k','c').replace('i','y'), '%b').month
                    fr_date = datetime.date(int(year), month, int(day)).strftime('%s')
                except:
                    fr_date=now
            else:
                fr_date = now
            for i in News.objects.filter(src='FR'):
                i.delete()
            fr_new=News(src='FR', date=fr_date, news=fr_news, last_checked=now)
            fr_new.save()
            dict_['FR_frame']=fr_news
        except Exception as e:
            dict_['FR_frame']='Freitagsrunden-Webseite nicht erreichbar! %s' % str(e)

    return dict_
