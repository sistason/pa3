import re


from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.http import HttpResponse, JsonResponse

from pa3_web.models import Subscriber


def get_subscriber(request):
    subscribers = Subscriber.objects.filter(identifier=Subscriber.request_to_identifier(request))

    return JsonResponse({'subscription': subscribers[0].serialize() if subscribers.exists() else None})


def subscribe(request):
    if not ('buffer' in request.POST and 'src' in request.POST and 'number' in request.POST):
        return HttpResponse(status=401, content='POST request incomplete!\n')

    identifier = Subscriber.request_to_identifier(request)
    subscriber = Subscriber.objects.get_or_create(identifier=identifier)
    subscriber.buffer = request.POST.get('buffer')
    subscriber.src = request.POST.get('src')
    subscriber.number = request.POST.get('number')
    subscriber.save()

    return JsonResponse({'subscription': subscriber.serialize()})


def delete_subscriber(request):
    [sub.delete() for sub in Subscriber.objects.filter(identifier=Subscriber.request_to_identifier(request))]
    return HttpResponse(200)
