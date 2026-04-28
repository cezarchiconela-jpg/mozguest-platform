from django.urls import path
from . import views

urlpatterns = [
    path('avaliar/<int:property_id>/', views.create_review, name='create_review'),
    path('favorito/<int:property_id>/', views.favorite_toggle, name='favorite_toggle'),
    path('meus-favoritos/', views.favorite_list, name='favorite_list'),
]
