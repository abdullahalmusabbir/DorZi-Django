from django.contrib import admin
from .models import TOrders

@admin.register(TOrders)
class TOrdersAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'customer',
        'tailor',
        'embroidery',
        'order_date',  
        'address',
        'contact_number',
        'gender',
        'occasion',
        'garment_type',
        'fabrics',
        'inspiration',
        'detailed_description',
        'special_requests',
        'delivery_date',
        'price',
        'chest',
        'waist',
        'hip',
        'shoulder',
        'sleeve',
        'neck',
        'length',
        'inseam',
        'measurements_confirmed',
        'fabric_selected',
        'cutting_started',
        'stitching_started',
        'deliver',
        'status',
        'meter',
        'selected_embroidery_info',
        'embroidery_total_price',
        'fabric_total_price',
    )
    list_filter = ('order_date', 'delivery_date', 'tailor', 'status')
    search_fields = (
        'customer__user__username',
        'tailor__business_name',
        'fabrics',
        'contact_number',
        'address',
    )
    
    # Make order_date read-only in change form
    readonly_fields = ('order_date',)

    fieldsets = (
        ('Customer & Tailor', {
            'fields': ('customer', 'tailor')
        }),
        ('Order Details', {
            'fields': ('gender', 'fabrics', 'detailed_description', 'special_requests', 'embroidery', 'price', 'occasion', 'garment_type', 'inspiration')
        }),
        ('Delivery Info', {
            'fields': ('address', 'contact_number', 'delivery_date')
        }),
        ('Measurements', {
            'fields': ('chest', 'waist', 'hip', 'shoulder', 'sleeve', 'neck', 'length', 'inseam', 'meter')
        }),
        ('Order Progress', {
            'fields': ('measurements_confirmed', 'fabric_selected', 'cutting_started', 'stitching_started', 'deliver', 'status')
        }),
        ('System Info', {
            'fields': ('order_date',)  # Now it's read-only so it's safe
        }),
    )
    
    # Optional: Auto-set order_date when creating new records
    def save_model(self, request, obj, form, change):
        if not change:  # If creating a new object
            # order_date will be automatically set by auto_now_add
            pass
        super().save_model(request, obj, form, change)
        