import json
import logging
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.permissions import AllowAny

from orders.models import Order
from .razorpay_client import verify_payment_signature, _get_client

logger = logging.getLogger(__name__)


class VerifyPaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        data = request.data
        rzp_order_id = data.get('razorpay_order_id')
        rzp_payment_id = data.get('razorpay_payment_id')
        rzp_signature = data.get('razorpay_signature')

        try:
            order = Order.objects.select_for_update().get(razorpay_order_id=rzp_order_id)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

        if order.payment_status == 'Paid':
            return Response({'message': 'Already processed'}, status=status.HTTP_200_OK)

        is_valid = verify_payment_signature(rzp_order_id, rzp_payment_id, rzp_signature)
        if not is_valid:
            order.payment_status = 'Failed'
            order.save()
            return Response({'error': 'Invalid payment signature'}, status=status.HTTP_400_BAD_REQUEST)

        # Mark paid and deduct stock
        order.payment_status = 'Paid'
        order.order_status = 'Processing'
        order.razorpay_payment_id = rzp_payment_id
        order.save()

        # Deduct stock for online payments
        for item in order.items.select_related('variant').all():
            if item.variant:
                variant = item.variant
                if variant.stock >= item.quantity:
                    variant.stock -= item.quantity
                    variant.save()

        return Response({'message': 'Payment verified successfully'}, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class RazorpayWebhookView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        webhook_secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', None)
        if not webhook_secret:
            return Response({'error': 'Webhook not configured'}, status=500)

        webhook_sig = request.headers.get('X-Razorpay-Signature')
        try:
            client = _get_client()
            client.utility.verify_webhook_signature(
                request.body.decode('utf-8'),
                webhook_sig,
                webhook_secret
            )
        except Exception as e:
            logger.error(f"Webhook signature failed: {e}")
            return Response({'error': 'Invalid signature'}, status=400)

        data = json.loads(request.body)
        event = data.get('event')
        entity = data.get('payload', {}).get('payment', {}).get('entity', {})
        rzp_order_id = entity.get('order_id')
        rzp_payment_id = entity.get('id')

        try:
            order = Order.objects.get(razorpay_order_id=rzp_order_id)
            if event == 'payment.captured' and order.payment_status != 'Paid':
                order.payment_status = 'Paid'
                order.order_status = 'Processing'
                order.razorpay_payment_id = rzp_payment_id
                order.save()
            elif event == 'payment.failed':
                order.payment_status = 'Failed'
                order.save()
        except Order.DoesNotExist:
            pass

        return Response({'status': 'handled'})