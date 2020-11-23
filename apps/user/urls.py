from django.urls import path, re_path
from apps.user.views import RegisterView, ActiveView, LoginView,LoginOutView, UserInfoView, UserOrderView, AddressView

urlpatterns = [
    path('register', RegisterView.as_view(), name='register'),
    re_path(r'active/(?P<token>.*)', ActiveView.as_view(), name='active'),
    path('login', LoginView.as_view(), name='login'),
    path('', UserInfoView.as_view(), name='user'),
    re_path(r'order/(?P<page>\d+)', UserOrderView.as_view(), name='order'),
    path('address', AddressView.as_view(), name='address'),
    path('logout', LoginOutView.as_view(), name='logout'),
]
