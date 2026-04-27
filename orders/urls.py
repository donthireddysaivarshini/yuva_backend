from django.urls import path
from .views import CheckoutView, OrderListView, order_detail

urlpatterns = [
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('', OrderListView.as_view(), name='order-list'),
    path('<int:pk>/', order_detail, name='order-detail'),
]