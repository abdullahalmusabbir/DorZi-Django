from django.contrib import admin
from .models import Customer

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'get_username',
        'phone',
        'address',
    )
    search_fields = (
        'user__username',  # যদি Customer model User এর সাথে OneToOne থাকে
        'phone',
        'address',
    )
    readonly_fields = ()

    fieldsets = (
        ('Measurements', {
            'fields': ('chest', 'waist', 'hip', 'shoulder', 'sleeve', 'neck', 'length', 'inseam')
        }),
        ('Contact Info', {
            'fields': ('phone', 'address', 'profile_picture')
        }),
    )

    def get_username(self, obj):
        # ধরলে Customer model এর সাথে User model linked via OneToOne
        return obj.user.username if hasattr(obj, 'user') else f'Customer #{obj.id}'
    get_username.short_description = 'Username'
