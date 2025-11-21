from django.contrib import admin
from .models import Reviews

@admin.register(Reviews)
class ReviewsAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'get_customer_username',
        'get_tailor_username', 
        'get_product_title',
        'rating',
        'get_short_comment',
        'timestamp',
    )
    list_filter = ('rating', 'timestamp', 'tailor')
    search_fields = (
        'customer__user__username', 
        'customer__user__first_name',
        'customer__user__last_name',
        'tailor__user__username', 
        'product__title', 
        'comment'
    )
    readonly_fields = ('timestamp',)
    list_per_page = 20

    fieldsets = (
        ('Reviewer Info', {
            'fields': ('customer', 'tailor', 'product')
        }),
        ('Review Details', {
            'fields': ('rating', 'comment')
        }),
        ('System Info', {
            'fields': ('timestamp',),
            'classes': ('collapse',)
        }),
    )

    def get_customer_username(self, obj):
        """Safely display customer username"""
        try:
            return obj.customer.user.username
        except AttributeError:
            return f"Customer-{obj.customer.id}"
    get_customer_username.short_description = 'Customer'
    get_customer_username.admin_order_field = 'customer__user__username'

    def get_tailor_username(self, obj):
        """Safely display tailor username"""
        if obj.tailor:
            try:
                return obj.tailor.user.username
            except AttributeError:
                return f"Tailor-{obj.tailor.id}"
        return "No Tailor"
    get_tailor_username.short_description = 'Tailor'
    get_tailor_username.admin_order_field = 'tailor__user__username'

    def get_product_title(self, obj):
        """Safely display product title"""
        if obj.product:
            return obj.product.title
        return "No Product"
    get_product_title.short_description = 'Product'
    get_product_title.admin_order_field = 'product__title'

    def get_short_comment(self, obj):
        """Display shortened comment"""
        if obj.comment:
            return obj.comment[:50] + "..." if len(obj.comment) > 50 else obj.comment
        return "No comment"
    get_short_comment.short_description = 'Comment'