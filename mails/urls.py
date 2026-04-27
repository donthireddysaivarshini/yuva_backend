from django.urls import path
from .views import BulkOrderFormView, ContactFormView, ComplaintFormView

urlpatterns = [
    path("bulk-order/", BulkOrderFormView.as_view(), name="bulk-order-form"),
    path("contact/", ContactFormView.as_view(), name="contact-form"),
    path("complaint/", ComplaintFormView.as_view(), name="complaint-form"),
]