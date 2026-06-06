from django.contrib import admin
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'customer_name',
        'customer_phone',
        'property',
        'room',
        'booking_type',
        'checkin_date',
        'checkout_date',
        'units_count',
        'unit_price',
        'estimated_amount',
        'status',
        'created_at',
    )

    list_filter = (
        'status',
        'booking_type',
        'checkin_date',
        'created_at',
    )

    search_fields = (
        'customer_name',
        'customer_phone',
        'customer_email',
        'property__name',
        'room__name',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
    )

from .models import AvailabilityBlock


@admin.register(AvailabilityBlock)
class AvailabilityBlockAdmin(admin.ModelAdmin):
    list_display = (
        'room',
        'start_datetime',
        'end_datetime',
        'reason',
        'created_by',
        'created_at',
    )

    list_filter = (
        'reason',
        'start_datetime',
        'created_at',
    )

    search_fields = (
        'room__name',
        'room__property__name',
        'notes',
    )
