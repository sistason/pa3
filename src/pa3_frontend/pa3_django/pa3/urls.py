
from django.urls import path, re_path

from pa3_web import views, news_handling, subscription_browser_handling
from pa3 import number_handling, statistics_handling

urlpatterns = [
    path('check_notify', views.check_notify),
    path('update_dump', views.update_dump),

    path('current_numbers', views.get_current_numbers_request),
    re_path(r'^api(?:/(?P<pa>.+)/?)?$', views.api),
    re_path(r'^api2/(?:(?P<paT>\d+)|(?P<ops>ops))?/?(?P<pa>.+?)?$', views.api2),

]

urlpatterns += [
    path('get_config', number_handling.get_config),
    path('write', number_handling.write),
]

urlpatterns += [
    path('recompute_stats', statistics_handling.recompute_stats),
    path('check_news', news_handling.check_news),
]

urlpatterns += [
    path('subscribe', subscription_browser_handling.subscribe),
    path('get_subscriber', subscription_browser_handling.get_subscriber),
    path('delete_subscriber', subscription_browser_handling.delete_subscriber),
]

# Keep this urlpattern at the end, since it matches everything not yet matched as src
urlpatterns += [
    re_path(r'^(?P<src>.+)?$', views.index)
]