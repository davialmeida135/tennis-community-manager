from django.urls import path
from . import views

urlpatterns = [
    path('api/auth/login', views.login, name='login'),
]