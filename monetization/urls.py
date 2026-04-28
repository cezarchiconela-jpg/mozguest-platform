from django.urls import path
from . import views

urlpatterns = [
    path('planos/', views.public_plan_list, name='public_plan_list'),
    path('planos/<int:plan_id>/solicitar/', views.request_plan, name='request_plan'),
    path('proprietario/subscricoes/', views.owner_subscription_list, name='owner_subscription_list'),

    path('admin/subscricoes/', views.admin_subscription_list, name='admin_subscription_list'),
    path('admin/subscricoes/<int:subscription_id>/activar/', views.admin_activate_subscription, name='admin_activate_subscription'),
    path('admin/subscricoes/<int:subscription_id>/cancelar/', views.admin_cancel_subscription, name='admin_cancel_subscription'),
]
