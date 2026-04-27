from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import BulkOrderFormSerializer, ContactFormSerializer, ComplaintFormSerializer

RECIPIENT = "info@yuvacomputers.in"


class BulkOrderFormView(APIView):
    def post(self, request):
        serializer = BulkOrderFormSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        subject = f"Bulk Order Request – {data['company']} ({data['quantity']} units)"
        html_body = render_to_string("contact/bulk_order_email.html", {"data": data})
        text_body = (
            f"Bulk Order Request\n\n"
            f"Name: {data['name']}\n"
            f"Company: {data['company']}\n"
            f"Email: {data['email']}\n"
            f"Phone: {data['phone']}\n"
            f"Device Type: {data['device_type']}\n"
            f"Quantity: {data['quantity']}\n"
            f"Requirements: {data.get('requirements', 'N/A')}\n"
        )

        msg = EmailMultiAlternatives(subject, text_body, settings.DEFAULT_FROM_EMAIL, [RECIPIENT])
        msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)

        return Response({"detail": "Your request has been submitted. We'll respond within 4 working hours."}, status=status.HTTP_200_OK)


class ContactFormView(APIView):
    def post(self, request):
        serializer = ContactFormSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        subject = f"Contact – {data['issue_type']} from {data['name']}"
        html_body = render_to_string("contact/contact_email.html", {"data": data})
        text_body = (
            f"Contact Form Submission\n\n"
            f"Name: {data['name']}\n"
            f"Email: {data['email']}\n"
            f"Phone: {data['phone']}\n"
            f"Order ID: {data.get('order_id', 'N/A')}\n"
            f"Issue Type: {data['issue_type']}\n"
            f"Message: {data['message']}\n"
        )

        msg = EmailMultiAlternatives(subject, text_body, settings.DEFAULT_FROM_EMAIL, [RECIPIENT])
        msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)

        return Response({"detail": "Message sent. We'll get back to you within 4 business hours."}, status=status.HTTP_200_OK)


class ComplaintFormView(APIView):
    def post(self, request):
        serializer = ComplaintFormSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        subject = f"Complaint – {data['issue_type']} | Order {data['order_id']}"
        html_body = render_to_string("contact/complaint_email.html", {"data": data})
        text_body = (
            f"Complaint / Feedback Submission\n\n"
            f"Name: {data['name']}\n"
            f"Order ID: {data['order_id']}\n"
            f"Issue Type: {data['issue_type']}\n"
            f"Email: {data['email']}\n"
            f"Phone: {data['phone']}\n"
            f"Description: {data['description']}\n"
        )

        msg = EmailMultiAlternatives(subject, text_body, settings.DEFAULT_FROM_EMAIL, [RECIPIENT])
        msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)

        return Response({"detail": "Complaint registered. Our team will reach out within 24 hours."}, status=status.HTTP_200_OK)