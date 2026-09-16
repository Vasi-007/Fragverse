from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        "order_number",
        "user",
        "total",
        "status",
        "created",
    )

    list_filter = (
        "status",
        "created",
    )

    search_fields = (
        "order_number",
        "user__username",
        "user__email",
        "razorpay_order_id",
        "razorpay_payment_id",
    )

    readonly_fields = (
        "order_number",
        "razorpay_order_id",
        "razorpay_payment_id",
        "created",
    )

    inlines = [OrderItemInline]