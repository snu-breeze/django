from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib import admin

urlpatterns = static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + patterns('',
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^talkback/', include('talkback.urls')),
    url(r'^hints/', include('zenaida.contrib.hints.urls')),
    url(r'^', include('brambling.urls')),
)
