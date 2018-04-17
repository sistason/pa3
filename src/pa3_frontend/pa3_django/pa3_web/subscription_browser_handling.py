import logging
from django.http import HttpResponse, JsonResponse

from pa3_web.models import Subscriber

logger = logging.getLogger(__name__)


def get_subscriber(request):
    subscribers = Subscriber.objects.filter(protocol='browser',
                                            identifier=Subscriber.http_request_to_identifier(request))

    return JsonResponse({'subscription': subscribers[0].serialize() if subscribers.exists() else None})


def delete_subscriber(request):
    [sub.delete() for sub in Subscriber.objects.filter(protocol='browser',
                                                       identifier=Subscriber.http_request_to_identifier(request))]
    return HttpResponse(200)


def subscribe(request):
    if not ('buffer' in request.GET and 'src' in request.GET and 'number' in request.GET and 'protocol' in request.GET):
        logger.info(request.GET)
        return HttpResponse(status=401, content='request incomplete!\n')

    identifier = Subscriber.http_request_to_identifier(request)
    protocol = request.GET.get('protocol')
    src = request.GET.get('src')
    buffer = request.GET.get('buffer')
    number = request.GET.get('number')

    subscribers = Subscriber.objects.filter(identifier=identifier, protocol=protocol, src=src)
    if not subscribers.exists():
        subscriber = Subscriber(identifier=identifier, protocol=protocol, src=src, buffer=buffer, number=number)
    else:
        subscriber = subscribers[0]
        subscriber.number = number
        subscriber.buffer = buffer
    subscriber.save()

    return JsonResponse({'subscription': subscriber.serialize()})
