from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    product_slug = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            'id', 'product_name', 'product_slug', 'variant_label',
            'price', 'quantity', 'image_url'
        ]

    def get_product_slug(self, obj):
        return obj.product.slug if obj.product else ''


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'first_name', 'last_name', 'phone', 'email',
            'shipping_address', 'apartment', 'landmark',
            'city', 'state', 'zip_code', 'country',
            'subtotal', 'discount_amount', 'shipping_fee',
            'cod_fee', 'tax_amount', 'total_amount', 'coupon_code',
            'payment_method', 'payment_status', 'order_status',
            'razorpay_order_id', 'tracking_link', 'tracking_note',
            'created_at', 'items',
        ]