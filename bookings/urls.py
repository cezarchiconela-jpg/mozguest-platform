from django.urls import path
from . import views

urlpatterns = [
    path('novo/<int:room_id>/', views.booking_create, name='booking_create'),
    path('sucesso/<int:booking_id>/', views.booking_success, name='booking_success'),

    path('cliente/minhas-reservas/', views.client_booking_list, name='client_booking_list'),
    path('cliente/minhas-reservas/<int:booking_id>/cancelar/', views.client_booking_cancel, name='client_booking_cancel'),

    path('proprietario/reservas/', views.owner_booking_list, name='owner_booking_list'),
    path('proprietario/reservas/<int:booking_id>/aceitar/', views.owner_booking_accept, name='owner_booking_accept'),
    path('proprietario/reservas/<int:booking_id>/rejeitar/', views.owner_booking_reject, name='owner_booking_reject'),
    path('proprietario/reservas/<int:booking_id>/concluir/', views.owner_booking_complete, name='owner_booking_complete'),
]
