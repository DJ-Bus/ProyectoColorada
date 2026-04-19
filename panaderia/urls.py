# panaderia/urls.py
from django.urls import path
from . import views

app_name = "panaderia"

urlpatterns = [
    # Ventas y Consumo
    path("", views.registrar_venta, name="registrar_venta"),
    path("corte/", views.corte_del_dia, name="corte_del_dia"),
    path("consumos/", views.registrar_consumo, name="registrar_consumo"),

    # Producción e inventario
    path("produccion/", views.registrar_produccion, name="registrar_produccion"),
    path("stock/", views.ver_stock, name="ver_stock"),
    path("conteo/", views.conteo_sucursal, name="conteo_sucursal"),
    path("tablero/", views.tablero_inventario, name="tablero_inventario"),

    # Compras
    path("compras/", views.registrar_compra, name="registrar_compra"),

    # Mayoreo
    path("mayoreo/nuevo/", views.crear_pedido, name="crear_pedido"),
    path("mayoreo/cerrar/<int:pedido_id>/", views.cerrar_pedido, name="cerrar_pedido"),
    path("mayoreo/", views.lista_pedidos, name="lista_pedidos"),

    # Pan Frío
    path("pan-frio/", views.pan_frio_lista, name="pan_frio_lista"),
]