from django.urls import path
from . import views

urlpatterns = [
    path('reserva/<int:booking_id>/pagar/', views.submit_payment, name='submit_payment'),

    path('proprietario/pagamentos/', views.owner_payment_list, name='owner_payment_list'),
    path('proprietario/financeiro/', views.owner_finance_dashboard, name='owner_finance_dashboard'),
    path('proprietario/financeiro/exportar/', views.owner_finance_export_csv, name='owner_finance_export_csv'),

    path('admin/financeiro/', views.admin_finance_dashboard, name='admin_finance_dashboard'),
    path('admin/financeiro/exportar/', views.admin_finance_export_csv, name='admin_finance_export_csv'),
]
