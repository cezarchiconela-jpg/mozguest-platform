from django.urls import path
from . import views

urlpatterns = [
    path('sobre/', views.about, name='about'),
    path('contacto/', views.contact, name='contact'),
    path('termos/', views.terms, name='terms'),
    path('privacidade/', views.privacy, name='privacy'),
    path('politica-cancelamento/', views.cancellation_policy, name='cancellation_policy'),
    path('politica-reembolso/', views.refund_policy, name='refund_policy'),
    path('regras-clientes/', views.client_rules, name='client_rules'),
    path('regras-proprietarios/', views.owner_rules, name='owner_rules'),
]
