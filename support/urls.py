from django.urls import path
from . import views

urlpatterns = [
    path('', views.support_ticket_list, name='support_ticket_list'),
    path('novo/', views.support_ticket_create, name='support_ticket_create'),
    path('<int:ticket_id>/', views.support_ticket_detail, name='support_ticket_detail'),

    path('proprietario/reclamacoes/', views.owner_support_ticket_list, name='owner_support_ticket_list'),

    path('admin/reclamacoes/', views.admin_support_ticket_list, name='admin_support_ticket_list'),
    path('admin/reclamacoes/<int:ticket_id>/', views.admin_support_ticket_detail, name='admin_support_ticket_detail'),
]
