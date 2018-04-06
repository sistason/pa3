import datetime
import logging
import time

from django.db.models import Sum
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from pa3.models import WaitingNumberBatch, WaitingNumber, NewestNumberBatch, StatisticalData


def get_src_statistic(_src):
    try:
        return StatisticalData.objects.get(src=_src)
    except MultipleObjectsReturned:
        for stats_ in StatisticalData.objects.filter(src=_src):
            stats_.delete()
    except ObjectDoesNotExist:
        pass
    except Exception as e:
        logging.exception('Exception while updating Stats: {}'.format(e))


def create_statistic(_src, ts):
    real_data_begin = int(datetime.date(2013, 9, 1).strftime("%s"))
    stat_ = StatisticalData(src=_src, date=ts)
    stat_qs = WaitingNumber.objects.filter(src=_src).filter(date__gt=real_data_begin).filter(
        date_delta__lt=60 * 60 * 3).filter(date_delta__gt=1)
    stat_.avg_len = stat_qs.count()
    stat_.avg_sum = stat_qs.aggregate(s=Sum('date_delta'))['s']
    if stat_.avg_sum is None:
        stat_.avg_sum = 0
        stat_.avg = 0
    else:
        stat_.avg = 1.0 * stat_.avg_sum / stat_.avg_len
    stat_.avg_last_two_weeks = stat_.avg
    stat_.avg_last_same_day = stat_.avg
    stat_.avg_whole = (stat_.avg + stat_.avg_last_two_weeks + stat_.avg_last_same_day) / 3

    stat_.avg_proc_delay_sum = stat_qs.aggregate(s=Sum('proc_delay'))['s']
    if stat_.avg_proc_delay_sum is None:
        stat_.avg_proc_delay_sum = 0
        stat_.avg_proc_delay_whole = 0
    else:
        stat_.avg_proc_delay_whole = 1.0 * stat_.avg_proc_delay_sum / stat_.avg_len

    stat_.save()


def update_statistic(_src, dd, new_batch, ts):
    stat_ = StatisticalData.objects.get(src=_src)
    stat_.avg_sum += dd
    stat_.avg_len += 1
    # sum/len = avg | sum=avg*len | new_avg = sum+dd/len+1
    stat_.avg = 1.0 * stat_.avg_sum / stat_.avg_len
    stat_.avg_whole = (stat_.avg + stat_.avg_last_two_weeks + stat_.avg_last_same_day) / 3

    if new_batch.proc_delay is not None and new_batch.proc_delay > 0:
        stat_.avg_proc_delay_sum += new_batch.proc_delay
        stat_.avg_proc_delay_len += 1
        stat_.avg_proc_delay_whole = 1.0 * stat_.avg_proc_delay_sum / stat_.avg_proc_delay_len

    stat_.date = ts
    stat_.save()


def recompute_stats(request):
    # Recomputes the last_two_weeks average and the last_day average
    # Requires calls, e.g. CRON
    real_data_begin = int(datetime.date(2013,5,1).strftime("%s"))

    for stat_data in StatisticalData.objects.all():
        # Get average over the last two weeks
        last_two_weeks_qs = WaitingNumber.objects.filter(
            src=stat_data.src).filter(
            date__gt=real_data_begin).filter(
            date_delta__lt=60*60*3).filter(
            date_delta__gt=1).filter(
            date__gt=int(time.time())-(60*60*24*14))
        last_two_weeks_len = last_two_weeks_qs.count()
        stat_data.avg_last_two_weeks = last_two_weeks_qs.aggregate(
            s=Sum('date_delta'))['s'] / last_two_weeks_len if last_two_weeks_len else 0

        # Get average from weekday last week (Tuesday last week)
        now = int(datetime.date.today().strftime('%s'))
        weekday_range = (now - (60*60*24*7), now + (24*60*60) - (60*60*24*7))
        last_sameday_qs = WaitingNumber.objects.filter(
            src=stat_data.src).filter(
            date__gt=real_data_begin).filter(
            date_delta__lt=60*60*3).filter(
            date_delta__gt=1).filter(
            date__range=weekday_range)
        last_sameday_len = last_sameday_qs.count()
        stat_data.avg_last_same_day = last_sameday_qs.aggregate(
            s=Sum('date_delta'))['s'] / last_sameday_len if last_sameday_len else 0

        # Weights of whole, last two weeks and last weekday are equal
        if last_two_weeks_len and last_sameday_len:
            stat_data.avg_whole = (stat_data.avg + stat_data.avg_last_two_weeks + stat_data.avg_last_same_day) / 3.0
        elif last_two_weeks_len:
            stat_data.avg_whole = (stat_data.avg + stat_data.avg_last_two_weeks) / 2.0
        elif last_sameday_len:
            stat_data.avg_whole = (stat_data.avg + stat_data.avg_last_same_day) / 2.0
        else:
            stat_data.avg_whole = stat_data.avg

        stat_data.save()
    return HttpResponse(status=200)