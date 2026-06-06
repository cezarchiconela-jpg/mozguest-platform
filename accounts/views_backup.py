from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
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
            return reverse_lazy('admin:index')

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
