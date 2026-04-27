#yuvacomputers
from decimal import Decimal
from django.db import transaction
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Order, OrderItem
from store.models import ProductVariant, SiteConfig, Coupon
from accounts.models import SavedAddress
from payments.razorpay_client import create_order as razorpay_create_order
from django.conf import settings

class CheckoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        cart_items = request.data.get('items', [])
        payment_method = request.data.get('payment_method')
        coupon_code = request.data.get('coupon_code')
        save_as_default = request.data.get('save_as_default', False)
        
        # 1. Basic Calculations
        subtotal = sum(Decimal(str(item['price'])) * item['quantity'] for item in cart_items)
        config = SiteConfig.objects.first()
        
        # 2. Handle Coupon
        discount = Decimal('0.00')
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code, active=True)
                if coupon.is_valid() and subtotal >= coupon.min_order_value:
                    if coupon.discount_type == 'percentage':
                        discount = (subtotal * coupon.value) / 100
                    else:
                        discount = coupon.value
                    coupon.uses_count += 1
                    coupon.save()
            except Coupon.DoesNotExist:
                pass # Or raise error if you want strict coupon enforcement

        # 3. Calculate Fees
        tax_amount = (subtotal - discount) * (config.tax_percentage / 100)
        shipping_cost = config.shipping_fee if (subtotal - discount) < config.free_shipping_threshold else 0
        cod_fee = (subtotal * config.cod_surcharge_percentage / 100) if payment_method == 'COD' else Decimal('0')
        
        final_total = subtotal - discount + tax_amount + shipping_cost + cod_fee

        with transaction.atomic():
            # Create Order
            order = Order.objects.create(
                user=request.user,
                total_amount=final_total,
                payment_method=payment_method,
                shipping_address=request.data.get('address')
            )
            
            # Save Address as default if requested
            if save_as_default:
                SavedAddress.objects.update_or_create(
                    user=request.user,
                    address=request.data.get('address'),
                    defaults={'is_default': True}
                )
            
            # Create Items & Deduct Stock
            for item in cart_items:
                variant = ProductVariant.objects.select_for_update().get(id=item['variant_id'])
                if variant.stock < item['quantity']:
                    return Response({"error": f"Insufficient stock for {variant.product.title}"}, status=status.HTTP_400_BAD_REQUEST)
                
                variant.stock -= item['quantity']
                variant.save()
                
                OrderItem.objects.create(
                    order=order, variant=variant, product_name=variant.product.title,
                    price=item['price'], quantity=item['quantity']
                )
            
            # Payment Handling
            if payment_method == 'Online':
                rp_order = razorpay_create_order(final_total)
                order.razorpay_order_id = rp_order['id']
                order.save()
                return Response({
                    'order_id': order.id, 
                    'razorpay_order_id': rp_order['id'], 
                    'amount': float(final_total),
                    'key': settings.RAZORPAY_KEY_ID
                })
                
            return Response({'order_id': order.id, 'status': 'COD Order Created'})