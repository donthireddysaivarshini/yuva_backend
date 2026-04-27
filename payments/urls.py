from django.urls import path
from .views import VerifyPaymentView # You will implement this later

urlpatterns = [
    path('verify/', VerifyPaymentView.as_view(), name='verify-payment'),
]