
from django.urls import path, re_path

from pa3_web import views, news_handling
from pa3 import number_handling
from pa3 import statistics_handling

urlpatterns = [
    path('check_notify', views.check_notify),
    path('update_dump', views.update_dump),

    path('current_numbers', views.get_current_numbers_request),
    re_path(r'^api(?:/(?P<pa>.+)/?)?$', views.api),
    re_path(r'^api2/(?:(?P<paT>\d+)|(?P<ops>ops))?/?(?P<pa>.+?)?$', views.api2),

]

urlpatterns += [
    path('write', number_handling.write),
    path('subscribe', number_handling.subscribe_client),
    path('recompute_stats', statistics_handling.recompute_stats),
    path('check_news', news_handling.check_news),
]

# Keep this urlpattern at the end, since it matches everything not yet matched as src
urlpatterns += [
    re_path(r'^(?P<src>.+)?$', views.index)
]