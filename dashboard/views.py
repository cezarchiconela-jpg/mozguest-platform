from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum
from django.shortcuts import redirect, render, get_object_or_404

from properties.models import Property, Room
from bookings.models import Booking
from reviews.models import Review
from payments.models import Payment


def home(request):
    featured_properties = Property.objects.filter(
        status='approved',
        is_featured=True
    )[:6]

    latest_properties = Property.objects.filter(
        status='approved'
    )[:8]

    context = {
        'featured_properties': featured_properties,
        'latest_properties': latest_properties,
    }

    return render(request, 'public/home.html', context)


@login_required
def owner_dashboard(request):
    if not hasattr(request.user, 'owner_profile'):
        messages.error(request, 'Apenas proprietários podem aceder ao painel de proprietário.')
        return redirect('home')

    my_properties = Property.objects.filter(owner=request.user)
    my_rooms = Room.objects.filter(property__owner=request.user)
    my_bookings = Booking.objects.filter(property__owner=request.user)

    context = {
        'total_properties': my_properties.count(),
        'approved_properties': my_properties.filter(status='approved').count(),
        'pending_properties': my_properties.filter(status='pending').count(),
        'total_rooms': my_rooms.count(),
        'total_bookings': my_bookings.count(),
        'pending_bookings': my_bookings.filter(status='pending').count(),
        'accepted_bookings': my_bookings.filter(status='accepted').count(),
        'completed_bookings': my_bookings.filter(status='completed').count(),
        'recent_properties': my_properties[:5],
        'recent_bookings': my_bookings[:5],
    }

    return render(request, 'owner/dashboard.html', context)


def is_staff_user(user):
    return user.is_authenticated and user.is_staff


@user_passes_test(is_staff_user)
def mozguest_admin_dashboard(request):
    properties = Property.objects.all()
    bookings = Booking.objects.all()
    reviews = Review.objects.all()
    payments = Payment.objects.all()

    context = {
        'total_properties': properties.count(),
        'pending_properties': properties.filter(status='pending').count(),
        'approved_properties': properties.filter(status='approved').count(),
        'rejected_properties': properties.filter(status='rejected').count(),

        'total_rooms': Room.objects.count(),

        'total_bookings': bookings.count(),
        'pending_bookings': bookings.filter(status='pending').count(),
        'accepted_bookings': bookings.filter(status='accepted').count(),
        'completed_bookings': bookings.filter(status='completed').count(),
        'cancelled_bookings': bookings.filter(status='cancelled').count(),

        'pending_reviews': reviews.filter(status='pending').count(),
        'approved_reviews': reviews.filter(status='approved').count(),

        'submitted_payments': payments.filter(status='submitted').count(),
        'confirmed_payments': payments.filter(status='confirmed').count(),
        'rejected_payments': payments.filter(status='rejected').count(),

        'total_paid': payments.filter(status='confirmed').aggregate(total=Sum('amount'))['total'] or 0,
        'total_commission': payments.filter(status='confirmed').aggregate(total=Sum('platform_commission_amount'))['total'] or 0,
        'total_owner_amount': payments.filter(status='confirmed').aggregate(total=Sum('owner_amount'))['total'] or 0,

        'recent_properties': properties.order_by('-created_at')[:8],
        'recent_bookings': bookings.order_by('-created_at')[:8],
        'recent_payments': payments.order_by('-created_at')[:8],
    }

    return render(request, 'admin_panel/dashboard.html', context)


@user_passes_test(is_staff_user)
def admin_property_approval(request):
    properties = Property.objects.filter(status='pending').order_by('-created_at')

    return render(request, 'admin_panel/property_approval.html', {
        'properties': properties
    })


@user_passes_test(is_staff_user)
def admin_approve_property(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id)
    property_obj.status = 'approved'
    property_obj.is_verified = True
    property_obj.save()

    messages.success(request, 'Propriedade aprovada e verificada com sucesso.')
    return redirect('mozguest_admin_properties')


@user_passes_test(is_staff_user)
def admin_reject_property(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id)
    property_obj.status = 'rejected'
    property_obj.save()

    messages.success(request, 'Propriedade rejeitada.')
    return redirect('mozguest_admin_properties')


@user_passes_test(is_staff_user)
def admin_review_approval(request):
    reviews = Review.objects.filter(status='pending').order_by('-created_at')

    return render(request, 'admin_panel/review_approval.html', {
        'reviews': reviews
    })


@user_passes_test(is_staff_user)
def admin_approve_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    review.status = 'approved'
    review.save()

    messages.success(request, 'Avaliação aprovada com sucesso.')
    return redirect('mozguest_admin_reviews')


@user_passes_test(is_staff_user)
def admin_reject_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    review.status = 'rejected'
    review.save()

    messages.success(request, 'Avaliação rejeitada.')
    return redirect('mozguest_admin_reviews')


@user_passes_test(is_staff_user)
def admin_payment_approval(request):
    payments = Payment.objects.filter(status='submitted').order_by('-created_at')

    return render(request, 'admin_panel/payment_approval.html', {
        'payments': payments
    })


@user_passes_test(is_staff_user)
def admin_confirm_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    payment.status = 'confirmed'
    payment.save()

    messages.success(request, 'Pagamento confirmado com sucesso.')
    return redirect('mozguest_admin_payments')


@user_passes_test(is_staff_user)
def admin_reject_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    payment.status = 'rejected'
    payment.save()

    messages.success(request, 'Pagamento rejeitado.')
    return redirect('mozguest_admin_payments')
