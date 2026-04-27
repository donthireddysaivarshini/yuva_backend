from django.db import models
from django.conf import settings
from store.models import Product, ProductVariant


class Order(models.Model):
    PAYMENT_STATUS = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Failed', 'Failed'),
        ('Refunded', 'Refunded'),
    ]
    ORDER_STATUS = [
        ('Processing', 'Processing'),
        ('Confirmed', 'Confirmed'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]
    PAYMENT_METHOD = [
        ('Online', 'Online'),
        ('COD', 'Cash on Delivery'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders'
    )
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    # Shipping
    shipping_address = models.TextField()
    apartment = models.CharField(max_length=255, blank=True)
    landmark = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default='India')

    # Financials
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cod_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    coupon_code = models.CharField(max_length=50, blank=True)

    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHOD, default='Online'
    )
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS, default='Pending'
    )
    order_status = models.CharField(
        max_length=20, choices=ORDER_STATUS, default='Processing'
    )

    # Razorpay
    razorpay_order_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)

    # Tracking
    tracking_link = models.URLField(max_length=500, blank=True, null=True)
    tracking_note = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} — {self.user.email}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(
        'store.Product', on_delete=models.SET_NULL, null=True, blank=True
    )
    variant = models.ForeignKey(
        'store.ProductVariant', on_delete=models.SET_NULL, null=True, blank=True
    )
    product_name = models.CharField(max_length=255)
    variant_label = models.CharField(max_length=100, blank=True)  # "8GB / 256GB SSD"
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    image_url = models.TextField(blank=True)

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"

    @property
    def total(self):
        return self.price * self.quantity