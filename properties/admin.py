from django.contrib import admin
from .models import Property, Room, PropertyPhoto


class RoomInline(admin.TabularInline):
    model = Room
    extra = 1


class PropertyPhotoInline(admin.TabularInline):
    model = PropertyPhoto
    extra = 1


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('name', 'property_type', 'city', 'neighbourhood', 'owner', 'status', 'is_verified', 'is_featured', 'created_at')
    list_filter = ('property_type', 'status', 'is_verified', 'is_featured', 'city')
    search_fields = ('name', 'city', 'neighbourhood', 'owner__username', 'owner__email')
    inlines = [RoomInline, PropertyPhotoInline]


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'property', 'room_type', 'capacity', 'price_hour', 'price_day', 'price_night', 'is_available')
    list_filter = ('room_type', 'is_available', 'has_ac', 'has_wifi', 'has_parking')
    search_fields = ('name', 'property__name')


@admin.register(PropertyPhoto)
class PropertyPhotoAdmin(admin.ModelAdmin):
    list_display = ('property', 'room', 'is_main', 'created_at')
    list_filter = ('is_main', 'created_at')
