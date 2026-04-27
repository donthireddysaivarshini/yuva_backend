from django.contrib import admin
from django.http import HttpResponse
from django.utils import timezone
from .models import Order, OrderItem
import csv


def export_to_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=orders.csv'
    writer = csv.writer(response)
    writer.writerow([
        'Order ID', 'Name', 'Email', 'Phone', 'Total',
        'Payment Method', 'Payment Status', 'Order Status',
        'City', 'State', 'Date'
    ])
    for o in queryset:
        writer.writerow([
            o.id, f"{o.first_name} {o.last_name}", o.email, o.phone,
            o.total_amount, o.payment_method, o.payment_status, o.order_status,
            o.city, o.state,
            timezone.localtime(o.created_at).strftime("%d-%m-%Y %H:%M")
        ])
    return response

export_to_csv.short_description = "Export selected to CSV"


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'variant_label', 'price', 'quantity']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'first_name', 'last_name', 'email', 'total_amount',
        'payment_method', 'payment_status', 'order_status', 'created_at'
    ]
    list_editable = ['order_status', 'payment_status']
    list_filter = ['payment_status', 'order_status', 'payment_method', 'created_at']
    search_fields = ['id', 'first_name', 'last_name', 'email', 'phone', 'razorpay_order_id']
    readonly_fields = ['created_at', 'updated_at', 'razorpay_order_id', 'razorpay_payment_id']
    actions = [export_to_csv]
    inlines = [OrderItemInline]
    fieldsets = (
        ('Customer', {'fields': (('first_name', 'last_name'), 'email', 'phone')}),
        ('Shipping', {'fields': ('shipping_address', 'apartment', 'landmark', 'city', 'state', 'zip_code', 'country')}),
        ('Financials', {'fields': ('subtotal', 'discount_amount', 'shipping_fee', 'cod_fee', 'tax_amount', 'total_amount', 'coupon_code')}),
        ('Payment', {'fields': ('payment_method', 'payment_status', 'order_status', 'razorpay_order_id', 'razorpay_payment_id')}),
        ('Tracking', {'fields': ('tracking_link', 'tracking_note')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )