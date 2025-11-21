from django.contrib import admin
from .models import Tailor

@admin.register(Tailor)
class TailorAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'business_name',
        'business_location',
        'phone',
        'expertise',
        'category',
        'price',
        'average_rating',
        'is_available',
        'total_earning',
        'tailor_about',
        'business_description',
        'district',
        'NID',
    )
    list_filter = ('expertise', 'category', 'is_available')
    search_fields = ('business_name', 'user__username', 'phone', 'NID')
    readonly_fields = ('average_rating', 'total_earning', 'purchased_products')

    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'business_name', 'business_location', 'phone', 'profile_picture', 'tailor_about', 'business_description', 'district')
        }),
        ('Professional Details', {
            'fields': ('expertise', 'category', 'services_offered', 'estimated_delivery_date', 'price', 'is_available')
        }),
        ('Identification', {
            'fields': ('NID',)
        }),
        ('Measurements', {
            'fields': ('Chest', 'waist', 'hip', 'shoulder', 'sleeve', 'neck', 'length', 'inseam')
        }),
        ('Statistics', {
            'fields': ('average_rating', 'total_earning', 'purchased_products')
        }),
    )
