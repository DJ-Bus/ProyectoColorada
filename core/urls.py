from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),

    # Autenticación
    path("login/", LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),

    # App principal — todo bajo /ventas/
    path("ventas/", include("panaderia.urls")),

    # Raíz redirige a /ventas/
    path("", RedirectView.as_view(url="/ventas/", permanent=False)),
]