from django.contrib import admin
from .models import Embroidery


@admin.register(Embroidery)
class EmbroideryAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'tailor',
        'fabric_type',
        'thread_type',
        'color',
        'complexity_level',
        'price',
        'estimated_time',
        'created_at',
        'updated_at',
    )
    list_filter = ('complexity_level', 'fabric_type', 'color', 'created_at')
    search_fields = ('title', 'description', 'tailor__business_name')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Basic Info', {
            'fields': ('tailor', 'title', 'description', 'design_image')
        }),
        ('Design Details', {
            'fields': ('fabric_type', 'thread_type', 'color', 'complexity_level')
        }),
        ('Pricing & Time', {
            'fields': ('price', 'estimated_time')
        }),
        ('System Info', {
            'fields': ('created_at', 'updated_at')
        }),
    )
