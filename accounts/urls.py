from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from .forms import Guest258PasswordResetForm, Guest258SetPasswordForm
from .views import (
    client_register,
    owner_register,
    CustomLoginView,
    logout_view,
    client_profile,
    owner_verification_profile,
    admin_owner_verification_list,
    admin_owner_verify,
    admin_owner_reject,
    admin_owner_suspend,
)

urlpatterns = [
    path('cadastro/cliente/', client_register, name='client_register'),
    path('cadastro/proprietario/', owner_register, name='owner_register'),
    path('login/', CustomLoginView.as_view(), name='login'),

    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt',
        form_class=Guest258PasswordResetForm,
        success_url=reverse_lazy('password_reset_done'),
    ), name='password_reset'),
    path('password-reset/enviado/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html',
    ), name='password_reset_done'),
    path('password-reset/confirmar/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html',
        form_class=Guest258SetPasswordForm,
        success_url=reverse_lazy('password_reset_complete'),
    ), name='password_reset_confirm'),
    path('password-reset/concluido/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html',
    ), name='password_reset_complete'),
    path('logout/', logout_view, name='logout'),
    path('cliente/perfil/', client_profile, name='client_profile'),
    path('proprietario/verificacao/', owner_verification_profile, name='owner_verification_profile'),
    path('258-admin/proprietarios/', admin_owner_verification_list, name='admin_owner_verification_list'),
    path('258-admin/proprietarios/<int:profile_id>/verificar/', admin_owner_verify, name='admin_owner_verify'),
    path('258-admin/proprietarios/<int:profile_id>/rejeitar/', admin_owner_reject, name='admin_owner_reject'),
    path('258-admin/proprietarios/<int:profile_id>/suspender/', admin_owner_suspend, name='admin_owner_suspend'),
]
