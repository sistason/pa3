
from django.urls import path, re_path

from pa3_web import views
from pa3 import number_handling

urlpatterns = [
    path('check_notify', views.check_notify),
    path('update_dump', views.update_dump),

    re_path(r'^(?P<src>.+)?$', views.index),
    re_path(r'^(?:numbers\.txt|api)/(?:(?P<paT>\d+)|(?P<ops>ops))?/?(?P<pa>.+?)?$', views.api),
    re_path(r'^api2/(?:(?P<paT>\d+)|(?P<ops>ops))?/?(?P<pa>.+?)?$', views.api2),
]

urlpatterns += [
    path('write', number_handling.write),
    path('subscribe', number_handling.subscribe_client),
    path('recompute_stats', number_handling.recompute_stats),
]

