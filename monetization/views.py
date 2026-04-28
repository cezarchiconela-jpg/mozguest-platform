from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

from notifications.services import notify_staff
from .models import CommercialPlan, OwnerSubscription


def is_staff_user(user):
    return user.is_authenticated and user.is_staff


def public_plan_list(request):
    plans = CommercialPlan.objects.filter(is_active=True)

    return render(request, 'monetization/plan_list.html', {
        'plans': plans
    })


@login_required
def request_plan(request, plan_id):
    if not hasattr(request.user, 'owner_profile'):
        messages.error(request, 'Apenas proprietários podem solicitar planos comerciais.')
        return redirect('home')

    plan = get_object_or_404(CommercialPlan, pk=plan_id, is_active=True)

    OwnerSubscription.objects.create(
        owner=request.user,
        plan=plan,
        status='pending'
    )

    notify_staff(
        title='Nova solicitação de plano comercial',
        message=f'O proprietário {request.user.username} solicitou o plano {plan.name}.',
        notification_type='system',
        link='/comercial/admin/subscricoes/'
    )

    messages.success(request, 'Pedido de plano enviado com sucesso. A MozGuest irá analisar.')
    return redirect('public_plan_list')


@login_required
def owner_subscription_list(request):
    if not hasattr(request.user, 'owner_profile'):
        messages.error(request, 'Apenas proprietários podem aceder a esta área.')
        return redirect('home')

    subscriptions = OwnerSubscription.objects.filter(owner=request.user).select_related('plan')

    return render(request, 'owner/subscription_list.html', {
        'subscriptions': subscriptions
    })


@user_passes_test(is_staff_user)
def admin_subscription_list(request):
    subscriptions = OwnerSubscription.objects.select_related('owner', 'plan').all()

    return render(request, 'admin_panel/subscription_list.html', {
        'subscriptions': subscriptions
    })


@user_passes_test(is_staff_user)
def admin_activate_subscription(request, subscription_id):
    subscription = get_object_or_404(OwnerSubscription, pk=subscription_id)
    subscription.status = 'active'
    subscription.save()

    messages.success(request, 'Subscrição activada com sucesso.')
    return redirect('admin_subscription_list')


@user_passes_test(is_staff_user)
def admin_cancel_subscription(request, subscription_id):
    subscription = get_object_or_404(OwnerSubscription, pk=subscription_id)
    subscription.status = 'cancelled'
    subscription.save()

    messages.success(request, 'Subscrição cancelada.')
    return redirect('admin_subscription_list')
