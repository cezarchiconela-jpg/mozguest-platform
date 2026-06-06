from django.urls import path
from . import views

urlpatterns = [
    path('', views.notification_list, name='notification_list'),
    path('<int:notification_id>/ler/', views.notification_read, name='notification_read'),
    path('marcar-todas/', views.notification_mark_all_read, name='notification_mark_all_read'),
]
