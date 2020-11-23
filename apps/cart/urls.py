from django.urls import path
from apps.cart.views import CartAddView, CartInfoView, CartUpdateView, CartDeleteView

urlpatterns = [
    path('add', CartAddView.as_view(), name='add'),
    path('', CartInfoView.as_view(), name='show'),
    path('update', CartUpdateView.as_view(), name='update'),
    path('delete', CartDeleteView.as_view(), name='delete'),
]
