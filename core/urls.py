from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    # Conectamos la ruta /ventas/ con nuestra app panaderia
    path('ventas/', include('panaderia.urls')),
    # Redirigimos la raíz (/) directamente a /ventas/
    path('', RedirectView.as_view(url='/ventas/', permanent=False)),
]