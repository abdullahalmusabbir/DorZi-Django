from django.contrib import admin
from .models import Fabric


@admin.register(Fabric)
class FabricAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'tailor',
        'fabric_type',
        'color',
        'pattern',
        'texture',
        'width',
        'length_available',
        'price_per_meter',
        'is_available',
        'created_at',
        'updated_at',
    )
    list_filter = (
        'fabric_type',
        'pattern',
        'color',
        'is_available',
        'created_at',
    )
    search_fields = (
        'name',
        'tailor__business_name',
        'color',
        'texture',
    )
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Basic Info', {
            'fields': ('tailor', 'name', 'description', 'image')
        }),
        ('Fabric Details', {
            'fields': ('fabric_type', 'color', 'pattern', 'texture')
        }),
        ('Measurements & Stock', {
            'fields': ('width', 'length_available', 'price_per_meter', 'is_available')
        }),
        ('System Info', {
            'fields': ('created_at', 'updated_at')
        }),
    )
