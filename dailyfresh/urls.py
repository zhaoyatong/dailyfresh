"""dailyfresh URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path, include
from django.views.static import serve
from dailyfresh.settings import MEDIA_ROOT

urlpatterns = [
    path('admin/', admin.site.urls),
    path('tinymce/', include('tinymce.urls')),
    path('search', include('haystack.urls')),
    path('user/', include(('apps.user.urls', 'user'), namespace='user')),
    path('cart/', include(('apps.cart.urls', 'cart'), namespace='cart')),
    path('order/', include(('apps.order.urls', 'order'), namespace='order')),
    path('', include(('apps.goods.urls', 'goods'), namespace='goods')),
    re_path(r'media/(?P<path>.*)$', serve, {'document_root': MEDIA_ROOT}),
]