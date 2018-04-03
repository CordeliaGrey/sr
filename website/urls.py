"""website URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from __future__ import print_function, absolute_import, division


from django.conf.urls import url
from django.contrib import admin

from sr.views import get_index, on_file_upload, is_finished, on_query_processed_image

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', get_index),
    url(r'^api/image', on_file_upload),
    url(r'^api/sr-finished', is_finished),
    url(r'^api/processed-image', on_query_processed_image)
]
