from django.urls import path, re_path
from apps.order.views import OrderPlaceView, OrderCommitView, OrderPayView, CommentView, BuyNowOrderPlaceView

urlpatterns = [
    path('place', OrderPlaceView.as_view(), name='place'),  # 提交订单页面显示
    path('commit', OrderCommitView.as_view(), name='commit'),  # 提交订单页面显示
    path('pay', OrderPayView.as_view(), name='pay'),  # 订单支付
    re_path(r'^comment/(?P<order_id>.+)$', CommentView.as_view(), name='comment'),  # 订单评论
    path('buynow', BuyNowOrderPlaceView.as_view(), name='buynow'),  # 订单评论
]
