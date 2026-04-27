from django.urls import path
from .views import VerifyPaymentView, RazorpayWebhookView

urlpatterns = [
    path('verify/', VerifyPaymentView.as_view(), name='verify-payment'),
    path('webhook/', RazorpayWebhookView.as_view(), name='razorpay-webhook'),
]