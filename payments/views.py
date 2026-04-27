from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db import transaction
from orders.models import Order
from .razorpay_client import verify_payment_signature

class VerifyPaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        order_id = request.data.get('order_id')
        razorpay_order_id = request.data.get('razorpay_order_id')
        razorpay_payment_id = request.data.get('razorpay_payment_id')
        razorpay_signature = request.data.get('razorpay_signature')

        # 1. Verify Signature
        is_valid = verify_payment_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature)

        if is_valid:
            with transaction.atomic():
                order = Order.objects.select_for_update().get(id=order_id)
                
                # ✅ IDEMPOTENCY CHECK
                if order.payment_status == 'Paid':
                    return Response({"status": "Already processed"}, status=status.HTTP_200_OK)
                
                # Finalize Order
                order.payment_status = 'Paid'
                order.order_status = 'Processing'
                order.razorpay_payment_id = razorpay_payment_id
                order.save()

                # Deduct Stock
                for item in order.items.all():
                    variant = item.variant
                    if variant.stock >= item.quantity:
                        variant.stock -= item.quantity
                        variant.save()
                    else:
                        raise Exception(f"Insufficient stock for {variant.product_name}")
            
            return Response({"status": "Payment Successful"}, status=status.HTTP_200_OK)
        
        return Response({"error": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST)