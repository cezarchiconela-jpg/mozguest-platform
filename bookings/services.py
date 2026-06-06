from datetime import datetime, timedelta
from decimal import Decimal
from .models import Booking, AvailabilityBlock


def combine_date_time(date_value, time_value, default_time):
    if not date_value:
        return None

    if not time_value:
        time_value = default_time

    return datetime.combine(date_value, time_value)


def get_booking_period(booking_type, checkin_date, checkin_time, checkout_date, checkout_time):
    if not checkin_date:
        return None, None

    if booking_type == 'hour':
        start = combine_date_time(checkin_date, checkin_time, datetime.min.time())

        if not checkout_time:
            return start, None

        end = combine_date_time(checkout_date or checkin_date, checkout_time, datetime.min.time())
        return start, end

    if booking_type == 'day':
        start = combine_date_time(checkin_date, checkin_time, datetime.min.time())
        end_date = checkout_date or checkin_date
        end = combine_date_time(end_date, checkout_time, datetime.max.time())
        return start, end

    if booking_type == 'night':
        start = combine_date_time(checkin_date, checkin_time, datetime.min.time())
        end_date = checkout_date or (checkin_date + timedelta(days=1))
        end = combine_date_time(end_date, checkout_time, datetime.max.time())
        return start, end

    if booking_type == 'month':
        start = combine_date_time(checkin_date, checkin_time, datetime.min.time())
        end_date = checkout_date or (checkin_date + timedelta(days=30))
        end = combine_date_time(end_date, checkout_time, datetime.max.time())
        return start, end

    return None, None


def calculate_units_count(booking_type, start, end):
    if not start or not end:
        return 1

    delta = end - start

    if delta.total_seconds() <= 0:
        return 0

    if booking_type == 'hour':
        hours = delta.total_seconds() / 3600
        return max(1, int(hours) if hours.is_integer() else int(hours) + 1)

    if booking_type == 'day':
        days = delta.days
        if delta.seconds > 0:
            days += 1
        return max(1, days)

    if booking_type == 'night':
        nights = delta.days
        return max(1, nights)

    if booking_type == 'month':
        days = delta.days
        months = days / 30
        return max(1, int(months) if months.is_integer() else int(months) + 1)

    return 1


def get_unit_price(room, booking_type):
    if booking_type == 'hour':
        return room.price_hour
    if booking_type == 'day':
        return room.price_day
    if booking_type == 'night':
        return room.price_night
    if booking_type == 'month':
        return room.price_month
    return None


def calculate_booking_amount(room, booking_type, checkin_date, checkin_time, checkout_date, checkout_time):
    start, end = get_booking_period(
        booking_type,
        checkin_date,
        checkin_time,
        checkout_date,
        checkout_time
    )

    unit_price = get_unit_price(room, booking_type)

    if unit_price is None:
        return None, 1, None, start, end

    units_count = calculate_units_count(booking_type, start, end)

    if units_count <= 0:
        return unit_price, 0, Decimal('0.00'), start, end

    estimated_amount = Decimal(unit_price) * Decimal(units_count)

    return unit_price, units_count, estimated_amount, start, end


def booking_has_conflict(room, start, end, exclude_booking_id=None):
    if not start or not end:
        return False

    active_bookings = Booking.objects.filter(
        room=room,
        status__in=['pending', 'accepted']
    )

    if exclude_booking_id:
        active_bookings = active_bookings.exclude(id=exclude_booking_id)

    for booking in active_bookings:
        existing_start, existing_end = get_booking_period(
            booking.booking_type,
            booking.checkin_date,
            booking.checkin_time,
            booking.checkout_date,
            booking.checkout_time
        )

        if not existing_start or not existing_end:
            continue

        overlap = start < existing_end and end > existing_start

        if overlap:
            return True

    blocks = AvailabilityBlock.objects.filter(room=room)

    for block in blocks:
        overlap = start < block.end_datetime.replace(tzinfo=None) and end > block.start_datetime.replace(tzinfo=None)

        if overlap:
            return True

    return False
