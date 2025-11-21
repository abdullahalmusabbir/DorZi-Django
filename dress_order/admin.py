from django.contrib import admin
from .models import Order

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'customer',
        'tailor',
        'product',
        'quantity',
        'price',
        'display_total_price',  # Custom method
        'status',
        'order_date',
        'delivery_date',
        'order_confirmed',
        'production',
        'quality_check',
        'deliver',
    )
    list_filter = ('status', 'size', 'order_date', 'delivery_date', 'tailor')
    search_fields = (
        'customer__username',
        'tailor__business_name',
        'product__title',
        'number',
        'address',
    )
    readonly_fields = ('order_date', 'display_total_price')

    fieldsets = (
        ('Order Info', {
            'fields': ('customer', 'tailor', 'product', 'quantity', 'price', 'size', 'category')
        }),
        ('Delivery Details', {
            'fields': ('address', 'number', 'delivery_date', 'status')
        }),
        ('Additional Information', {
            'fields': ('special_instructions',)
        }),
        ('System Info', {
            'fields': ('order_date', 'display_total_price')
        }),
        ('Order Progress', {
            'fields': ('order_confirmed', 'production', 'quality_check', 'deliver')
        }),
    )

    def display_total_price(self, obj):
        """Safe display of total price that handles None values"""
        if obj.quantity is not None and obj.price is not None:
            return obj.quantity * obj.price
        return "N/A"
    display_total_price.short_description = 'Total Price'