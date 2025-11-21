from django.contrib import admin
from .models import FavoriteDress


@admin.register(FavoriteDress)
class FavoriteDressAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'dress',
        'added_on',
    )
    list_filter = ('added_on', 'dress')
    search_fields = (
        'user__user__username',   # Customer model যদি User এর সাথে OneToOne থাকে
        'dress__title',
        'dress__tailor__business_name',
    )
    readonly_fields = ('added_on',)

    fieldsets = (
        ('Favorite Info', {
            'fields': ('user', 'dress')
        }),
        ('System Info', {
            'fields': ('added_on',)
        }),
    )
