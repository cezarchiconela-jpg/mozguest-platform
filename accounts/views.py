from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.db import models
from .forms import (
    OwnerRegistrationForm,
    ClientRegistrationForm,
    ClientProfileForm,
    LoginForm
)
from .models import ClientProfile


def client_register(request):
    if request.method == 'POST':
        form = ClientRegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()
            user.backend = 'accounts.backends.EmailOrUsernameBackend'
            login(request, user)
            messages.success(request, 'Conta de cliente criada com sucesso.')
            return redirect('home')
    else:
        form = ClientRegistrationForm()

    return render(request, 'accounts/client_register.html', {
        'form': form
    })


def owner_register(request):
    if request.method == 'POST':
        form = OwnerRegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()
            user.backend = 'accounts.backends.EmailOrUsernameBackend'
            login(request, user)
            messages.success(request, 'Conta de proprietário criada com sucesso.')
            return redirect('owner_dashboard')
    else:
        form = OwnerRegistrationForm()

    return render(request, 'accounts/owner_register.html', {
        'form': form
    })


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = LoginForm

    def get_success_url(self):
        user = self.request.user

        if user.is_staff:
            return reverse_lazy('guest258_admin_dashboard')

        if hasattr(user, 'owner_profile'):
            return reverse_lazy('owner_dashboard')

        return reverse_lazy('home')


def logout_view(request):
    logout(request)
    messages.success(request, 'Sessão terminada com sucesso.')
    return redirect('home')


@login_required
def client_profile(request):
    if hasattr(request.user, 'owner_profile') and not hasattr(request.user, 'client_profile'):
        messages.error(request, 'Esta área é destinada ao perfil de cliente.')
        return redirect('owner_dashboard')

    profile, created = ClientProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ClientProfileForm(request.POST, instance=profile, user=request.user)

        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado com sucesso.')
            return redirect('client_profile')
    else:
        form = ClientProfileForm(instance=profile, user=request.user)

    return render(request, 'accounts/client_profile.html', {
        'form': form
    })


@login_required
def owner_verification_profile(request):
    if not hasattr(request.user, 'owner_profile'):
        messages.error(request, 'Apenas proprietários podem aceder à verificação.')
        return redirect('home')

    from .forms import OwnerKYCForm
    profile = request.user.owner_profile

    if request.method == 'POST':
        form = OwnerKYCForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Dados de verificação enviados para análise da +258 Guest.')
            return redirect('owner_verification_profile')
    else:
        form = OwnerKYCForm(instance=profile, user=request.user)

    return render(request, 'accounts/owner_verification.html', {
        'form': form,
        'profile': profile,
    })


from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from django.utils import timezone
from notifications.services import create_notification
from dashboard.services import log_audit
from .models import OwnerProfile


def is_staff_user(user):
    return user.is_authenticated and user.is_staff


@user_passes_test(is_staff_user)
def admin_owner_verification_list(request):
    status = request.GET.get('status', 'pending').strip()
    query = request.GET.get('q', '').strip()
    valid = {choice[0] for choice in OwnerProfile.VERIFICATION_STATUS}

    owners = OwnerProfile.objects.select_related('user', 'verified_by').order_by('-updated_at')
    if status in valid:
        owners = owners.filter(verification_status=status)
    elif status == 'all':
        status = 'all'
    else:
        status = 'pending'
        owners = owners.filter(verification_status__in=['pending', 'in_review'])

    if query:
        owners = owners.filter(
            models.Q(user__username__icontains=query) |
            models.Q(user__email__icontains=query) |
            models.Q(business_name__icontains=query) |
            models.Q(nuit__icontains=query) |
            models.Q(document_number__icontains=query)
        )

    return render(request, 'admin_panel/owner_verification_list.html', {
        'owners': owners,
        'status': status,
        'query': query,
        'status_choices': OwnerProfile.VERIFICATION_STATUS,
        'pending_count': OwnerProfile.objects.filter(verification_status__in=['pending', 'in_review']).count(),
        'verified_count': OwnerProfile.objects.filter(verification_status='verified').count(),
        'rejected_count': OwnerProfile.objects.filter(verification_status='rejected').count(),
        'suspended_count': OwnerProfile.objects.filter(verification_status='suspended').count(),
    })


@user_passes_test(is_staff_user)
@require_POST
def admin_owner_verify(request, profile_id):
    profile = get_object_or_404(OwnerProfile.objects.select_related('user'), pk=profile_id)
    notes = request.POST.get('verification_notes', '').strip()
    profile.verification_status = 'verified'
    profile.verified_by = request.user
    profile.verified_at = timezone.now()
    if notes:
        profile.verification_notes = notes
    profile.save(update_fields=['verification_status', 'verified_by', 'verified_at', 'verification_notes', 'updated_at'])
    create_notification(profile.user, 'Proprietário verificado', 'A +258 Guest verificou a sua conta de proprietário.', notification_type='account', link='/proprietario/verificacao/')
    log_audit('owner_verified', request=request, target=profile, message='Proprietário verificado pela administração.')
    messages.success(request, 'Proprietário verificado com sucesso.')
    return redirect('admin_owner_verification_list')


@user_passes_test(is_staff_user)
@require_POST
def admin_owner_reject(request, profile_id):
    profile = get_object_or_404(OwnerProfile.objects.select_related('user'), pk=profile_id)
    notes = request.POST.get('verification_notes', '').strip()
    profile.verification_status = 'rejected'
    if notes:
        profile.verification_notes = notes
    profile.save(update_fields=['verification_status', 'verification_notes', 'updated_at'])
    create_notification(profile.user, 'Verificação rejeitada', 'A verificação da sua conta foi rejeitada. Reveja os dados e documentos.', notification_type='account', link='/proprietario/verificacao/')
    log_audit('owner_rejected', request=request, target=profile, message='Verificação do proprietário rejeitada.', metadata={'notes': notes})
    messages.success(request, 'Verificação rejeitada.')
    return redirect('admin_owner_verification_list')


@user_passes_test(is_staff_user)
@require_POST
def admin_owner_suspend(request, profile_id):
    profile = get_object_or_404(OwnerProfile.objects.select_related('user'), pk=profile_id)
    notes = request.POST.get('verification_notes', '').strip()
    profile.verification_status = 'suspended'
    if notes:
        profile.verification_notes = notes
    profile.save(update_fields=['verification_status', 'verification_notes', 'updated_at'])
    create_notification(profile.user, 'Conta de proprietário suspensa', 'A sua conta de proprietário foi suspensa para análise.', notification_type='account', link='/proprietario/verificacao/')
    log_audit('owner_suspended', request=request, target=profile, message='Proprietário suspenso.', metadata={'notes': notes})
    messages.success(request, 'Proprietário suspenso.')
    return redirect('admin_owner_verification_list')
