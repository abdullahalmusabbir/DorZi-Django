from django.contrib import admin
from django.utils.html import format_html
from .models import PreDesigned, Image


class ImageInline(admin.TabularInline):
    model = Image
    extra = 1
    fields = ('image', 'image_preview')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="100" style="object-fit: cover;" />', obj.image.url)
        return "No Image"
    
    image_preview.short_description = 'Preview'


@admin.register(PreDesigned)
class PreDesignedAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'tailor',
        'price',
        'availability',
        'category',
        'gender',
        'fabric_type',
        'color',
        'is_available',
        'created_at',
    )
    
    list_filter = (
        'category', 
        'fabric_type', 
        'color', 
        'gender',
        'created_at',
        'availability'
    )
    
    search_fields = (
        'title', 
        'description', 
        'tailor__business_name',
        'fabric_type',
        'color'
    )
    
    list_editable = ('price', 'availability')
    
    inlines = [ImageInline]
    
    readonly_fields = (
        'created_at', 
        'updated_at',
        'display_images'
    )
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'tailor', 
                'title', 
                'description', 
                'category',
                'gender'
            )
        }),
        ('Pricing & Stock', {
            'fields': (
                'price', 
                'availability'
            )
        }),
        ('Material & Design Details', {
            'fields': (
                'fabric_type', 
                'thread_type', 
                'color', 
                'estimated_time'
            )
        }),
        ('Images', {
            'fields': ('display_images',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at', 
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def is_available(self, obj):
        return obj.availability > 0
    
    is_available.boolean = True
    is_available.short_description = 'Available'
    
    def display_images(self, obj):
        images = obj.images.all()
        if images:
            image_html = ''
            for image in images:
                image_html += format_html(
                    '<div style="float: left; margin: 5px;">'
                    '<img src="{}" width="150" height="150" style="object-fit: cover; border: 1px solid #ddd;" />'
                    '</div>',
                    image.image.url
                )
            return format_html('<div style="overflow: hidden;">{}</div>', image_html)
        return "No images available"
    
    display_images.short_description = 'Product Images'
    
    list_per_page = 20
    
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('tailor')


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = (
        'predesigned',
        'image_preview',
        'tailor_name'
    )
    
    search_fields = (
        'predesigned__title',
        'predesigned__tailor__business_name'
    )
    
    list_filter = ('predesigned__category',)
    
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="100" height="100" style="object-fit: cover;" />', 
                obj.image.url
            )
        return "No Image"
    
    image_preview.short_description = 'Preview'
    
    def tailor_name(self, obj):
        return obj.predesigned.tailor.business_name
    
    tailor_name.short_description = 'Tailor'
    
    list_per_page = 20