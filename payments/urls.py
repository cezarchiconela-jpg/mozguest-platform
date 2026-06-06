from django.urls import path
from . import views

urlpatterns = [
    path('reserva/<int:booking_id>/pagar/', views.submit_payment, name='submit_payment'),
    path('reserva/<int:booking_id>/gateway/<str:gateway_name>/iniciar/', views.start_gateway_payment, name='start_gateway_payment'),
    path('transaccao/<int:transaction_id>/', views.payment_transaction_status, name='payment_transaction_status'),
    path('recibo/<int:payment_id>/', views.payment_receipt, name='payment_receipt'),
    path('transaccao/<int:transaction_id>/consultar/', views.check_gateway_payment_status, name='check_gateway_payment_status'),
    path('transaccao/<int:transaction_id>/simular-sucesso/', views.simulate_gateway_payment_success, name='simulate_gateway_payment_success'),
    path('webhook/<str:gateway_name>/', views.payment_gateway_webhook, name='payment_gateway_webhook'),

    path('proprietario/pagamentos/', views.owner_payment_list, name='owner_payment_list'),
    path('proprietario/financeiro/', views.owner_finance_dashboard, name='owner_finance_dashboard'),
    path('proprietario/financeiro/exportar/', views.owner_finance_export_csv, name='owner_finance_export_csv'),

    path('proprietario/liquidacoes/', views.owner_payout_list, name='owner_payout_list'),
    path('proprietario/liquidacoes/<int:payout_id>/recibo/', views.payout_receipt, name='payout_receipt'),

    path('admin/liquidacoes/', views.admin_payout_list, name='admin_owner_payout_list'),
    path('admin/relatorio-diario/', views.admin_daily_finance_report, name='admin_daily_finance_report'),
    path('admin/cancelamentos-reembolsos/', views.admin_refund_review_list, name='admin_refund_review_list'),
    path('admin/cancelamentos-reembolsos/<int:booking_id>/rever/', views.admin_review_refund, name='admin_review_refund'),
    path('admin/liquidacoes/exportar/', views.admin_payout_export_csv, name='admin_owner_payout_export_csv'),
    path('admin/liquidacoes/sincronizar/', views.admin_sync_missing_payouts, name='admin_sync_missing_payouts'),
    path('admin/liquidacoes/<int:payout_id>/pagar/', views.admin_mark_payout_paid, name='admin_mark_payout_paid'),
    path('admin/liquidacoes/<int:payout_id>/reter/', views.admin_hold_payout, name='admin_hold_payout'),

    path('admin/financeiro/', views.admin_finance_dashboard, name='admin_finance_dashboard'),
    path('admin/financeiro/exportar/', views.admin_finance_export_csv, name='admin_finance_export_csv'),
    path('admin/transaccoes/', views.admin_transaction_list, name='admin_payment_transaction_list'),
]
