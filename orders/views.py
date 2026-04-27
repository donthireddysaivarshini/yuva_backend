from decimal import Decimal
from django.db import transaction
from django.conf import settings
from django.utils import timezone
from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes

from .models import Order, OrderItem
from .serializers import OrderSerializer
from store.models import Product, ProductVariant, SiteConfig, Coupon
from accounts.models import SavedAddress
from payments.razorpay_client import create_order as razorpay_create_order


class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).prefetch_related('items').order_by('-created_at')


class CheckoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        data = request.data
        cart_items = data.get('items', [])
        payment_method = data.get('payment_method', 'Online')
        coupon_code = data.get('coupon_code', '').strip().upper()
        save_as_default = data.get('save_as_default', False)

        if not cart_items:
            return Response(
                {'error': 'Cart is empty'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ── 1. Load site config ──────────────────────────────────────────────
        config = SiteConfig.objects.first()
        shipping_flat = Decimal(str(config.shipping_fee)) if config else Decimal('0')
        free_threshold = Decimal(str(config.free_shipping_threshold)) if config else Decimal('0')
        cod_pct = Decimal(str(config.cod_surcharge_percentage)) if config else Decimal('2')
        tax_pct = Decimal(str(config.tax_percentage)) if config else Decimal('0')

        # ── 2. Validate cart items & calculate subtotal ──────────────────────
        order_line_items = []
        subtotal = Decimal('0.00')

        for item in cart_items:
            variant_id = item.get('variant_id')
            product_id = item.get('product_id')
            quantity = int(item.get('quantity', 1))
            client_price = Decimal(str(item.get('price', 0)))

            try:
                if variant_id:
                    variant = ProductVariant.objects.select_for_update().get(id=variant_id)
                    product = variant.product
                    server_price = product.price + variant.price_override
                    variant_label = f"{variant.ram} / {variant.storage}"
                    if variant.stock < quantity:
                        return Response(
                            {'error': f'Insufficient stock for {product.title} ({variant_label})'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                else:
                    product = Product.objects.get(id=product_id)
                    variant = None
                    server_price = product.price
                    variant_label = ''

                # Use server price (ignore client price to prevent tampering)
                line_total = server_price * quantity
                subtotal += line_total

                # Get product image
                primary_img = product.images.filter(is_primary=True).first() or product.images.first()
                img_url = request.build_absolute_uri(primary_img.image.url) if primary_img else ''

                order_line_items.append({
                    'product': product,
                    'variant': variant,
                    'product_name': product.title,
                    'variant_label': variant_label,
                    'price': server_price,
                    'quantity': quantity,
                    'image_url': img_url,
                })
            except (ProductVariant.DoesNotExist, Product.DoesNotExist):
                return Response(
                    {'error': f'Product not found'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # ── 3. Coupon validation ─────────────────────────────────────────────
        discount_amount = Decimal('0.00')
        coupon_obj = None

        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code, active=True)
                now = timezone.now()
                if coupon.valid_from > now or coupon.valid_to < now:
                    return Response(
                        {'error': 'Coupon has expired'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                if coupon.uses_count >= coupon.usage_limit:
                    return Response(
                        {'error': 'Coupon usage limit reached'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                if subtotal < coupon.min_order_value:
                    return Response(
                        {'error': f'Minimum order of ₹{coupon.min_order_value} required'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                if coupon.discount_type == 'percentage':
                    discount_amount = (subtotal * coupon.value) / 100
                else:
                    discount_amount = coupon.value
                coupon_obj = coupon
            except Coupon.DoesNotExist:
                return Response(
                    {'error': 'Invalid coupon code'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # ── 4. Fee calculations ──────────────────────────────────────────────
        taxable = max(Decimal('0'), subtotal - discount_amount)
        tax_amount = (taxable * tax_pct) / 100

        if free_threshold > 0 and subtotal >= free_threshold:
            shipping_fee = Decimal('0.00')
        else:
            shipping_fee = shipping_flat

        cod_fee = (subtotal * cod_pct / 100) if payment_method == 'COD' else Decimal('0.00')

        total_amount = taxable + tax_amount + shipping_fee + cod_fee

        # ── 5. Shipping address fields ───────────────────────────────────────
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        phone = data.get('phone', '')
        address = data.get('address', '')
        apartment = data.get('apartment', '')
        landmark = data.get('landmark', '')
        city = data.get('city', '')
        state = data.get('state', '')
        zip_code = data.get('zip_code', '')
        country = data.get('country', 'India')

        # ── 6. Create order atomically ───────────────────────────────────────
        try:
            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user,
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone,
                    email=request.user.email,
                    shipping_address=address,
                    apartment=apartment,
                    landmark=landmark,
                    city=city,
                    state=state,
                    zip_code=zip_code,
                    country=country,
                    subtotal=subtotal,
                    discount_amount=discount_amount,
                    shipping_fee=shipping_fee,
                    cod_fee=cod_fee,
                    tax_amount=tax_amount,
                    total_amount=total_amount,
                    coupon_code=coupon_code,
                    payment_method=payment_method,
                    payment_status='Pending',
                    order_status='Processing' if payment_method == 'COD' else 'Pending',
                )

                for item in order_line_items:
                    OrderItem.objects.create(
                        order=order,
                        product=item['product'],
                        variant=item['variant'],
                        product_name=item['product_name'],
                        variant_label=item['variant_label'],
                        price=item['price'],
                        quantity=item['quantity'],
                        image_url=item['image_url'],
                    )
                    # Deduct stock immediately for COD
                    if payment_method == 'COD' and item['variant']:
                        v = item['variant']
                        v.stock -= item['quantity']
                        v.save()

                # Save as default address
                if save_as_default:
                    SavedAddress.objects.filter(
                        user=request.user, is_default=True
                    ).update(is_default=False)
                    SavedAddress.objects.create(
                        user=request.user,
                        label='Home',
                        first_name=first_name,
                        last_name=last_name,
                        address=address,
                        apartment=apartment,
                        landmark=landmark,
                        city=city,
                        state=state,
                        zip_code=zip_code,
                        country=country,
                        phone=phone,
                        is_default=True,
                    )

                # Increment coupon usage
                if coupon_obj:
                    coupon_obj.uses_count += 1
                    coupon_obj.save()

                # COD — done
                if payment_method == 'COD':
                    return Response({
                        'order_id': order.id,
                        'payment_method': 'COD',
                        'message': 'Order placed successfully! Our team will contact you.',
                        'total_amount': float(total_amount),
                    }, status=status.HTTP_201_CREATED)

                # Online — create Razorpay order
                rzp_order = razorpay_create_order(total_amount)
                order.razorpay_order_id = rzp_order['id']
                order.save()

                return Response({
                    'order_id': order.id,
                    'razorpay_order_id': rzp_order['id'],
                    'amount': rzp_order['amount'],
                    'currency': 'INR',
                    'key': settings.RAZORPAY_KEY_ID,
                    'payment_method': 'Online',
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def order_detail(request, pk):
    try:
        order = Order.objects.prefetch_related('items').get(pk=pk, user=request.user)
        return Response(OrderSerializer(order).data)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=404)