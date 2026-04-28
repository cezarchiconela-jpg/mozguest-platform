from django.urls import path
from . import views

urlpatterns = [
    path('', views.conversation_list, name='conversation_list'),
    path('reserva/<int:booking_id>/', views.start_conversation_from_booking, name='start_conversation_from_booking'),
    path('<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
]
