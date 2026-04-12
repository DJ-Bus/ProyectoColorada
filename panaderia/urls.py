# panaderia/urls.py
from django.urls import path
from . import views

app_name = 'panaderia'

urlpatterns = [
    path('', views.dashboard_ventas, name='dashboard_ventas'),
]