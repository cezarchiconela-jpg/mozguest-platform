from django.contrib import admin
from .models import Review, Favorite


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        'property',
        'customer_name',
        'rating',
        'status',
        'created_at',
    )

    list_filter = (
        'status',
        'rating',
        'created_at',
    )

    search_fields = (
        'property__name',
        'customer_name',
        'comment',
    )


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'property',
        'created_at',
    )

    search_fields = (
        'user__username',
        'property__name',
    )
