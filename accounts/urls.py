from django.urls import path
from .views import (
    client_register,
    owner_register,
    CustomLoginView,
    logout_view,
    client_profile,
)

urlpatterns = [
    path('cadastro/cliente/', client_register, name='client_register'),
    path('cadastro/proprietario/', owner_register, name='owner_register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('cliente/perfil/', client_profile, name='client_profile'),
]
