
from django.http import HttpResponse, JsonResponse

from pa3_web.models import Subscriber

#
# Example of a subscription client
#


def delete_subscriber(phone_number):
    [sub.delete() for sub in Subscriber.objects.filter(protocol='sms',
                                                       identifier=phone_number)]
    return HttpResponse(200)

def notify(subscriber):
    # Send Notifying SMS
    return