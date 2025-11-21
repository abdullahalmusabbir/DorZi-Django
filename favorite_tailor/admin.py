from django.contrib import admin
from .models import FavoriteTailor


@admin.register(FavoriteTailor)
class FavoriteTailorAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'tailor',
        'added_on',
    )
    list_filter = ('added_on', 'tailor')
    search_fields = (
        'user__user__username',   # Customer model যদি User এর সাথে OneToOne থাকে
        'tailor__business_name',
        'tailor__user__username'
    )
    readonly_fields = ('added_on',)

    fieldsets = (
        ('Favorite Info', {
            'fields': ('user', 'tailor')
        }),
        ('System Info', {
            'fields': ('added_on',)
        }),
    )
