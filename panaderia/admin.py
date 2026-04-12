from django.contrib import admin
from django.utils.html import format_html # <-- Importamos esto para inyectar color
from .models import (
    Insumo, Producto, Empleado,
    ProduccionDiaria, CompraInsumo,
    VentaSucursal, PedidoMayoreo, PanFrio,
)

admin.site.site_header  = "Administración - Panadería La Colorada"
admin.site.site_title   = "La Colorada ERP"
admin.site.index_title  = "Panel de Control Principal"

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display   = ("nombre", "precio_publico", "precio_mayoreo", "stock_sucursal", "es_temporada")
    search_fields  = ("nombre",)
    list_filter    = ("es_temporada", "activo")

@admin.register(PedidoMayoreo)
class PedidoMayoreoAdmin(admin.ModelAdmin):
    list_display   = (
        "empleado", "producto", "fecha",
        "cantidad_entregada", "cantidad_regresada",
        "piezas_vendidas_col", "monto_recibido", "diferencia_col",
    )
    list_filter    = ("fecha", "empleado")

    @admin.display(description="Piezas vendidas")
    def piezas_vendidas_col(self, obj):
        return obj.piezas_vendidas

    @admin.display(description="Diferencia $")
    def diferencia_col(self, obj):
        d = obj.diferencia
        # Rojo si falta dinero, verde si está bien
        color = "red" if d > 0 else "green"
        # Inyectamos el color directamente en el HTML de la tabla
        return format_html('<span style="color: {}; font-weight: bold;">${:.2f}</span>', color, d)

@admin.register(VentaSucursal)
class VentaSucursalAdmin(admin.ModelAdmin):
    list_display   = ("fecha", "empleado", "monto", "notas")
    list_filter    = ("fecha", "empleado")
    date_hierarchy = "fecha"        # navegador por día/mes/año arriba de la tabla

@admin.register(ProduccionDiaria)
class ProduccionDiariaAdmin(admin.ModelAdmin):
    list_display   = ("fecha", "producto", "piezas_producidas")
    list_filter    = ("producto",)
    date_hierarchy = "fecha"

@admin.register(CompraInsumo)
class CompraInsumoAdmin(admin.ModelAdmin):
    list_display   = ("fecha", "insumo", "cantidad", "costo_total")
    date_hierarchy = "fecha"

admin.site.register(Insumo)
admin.site.register(Empleado)
admin.site.register(PanFrio)