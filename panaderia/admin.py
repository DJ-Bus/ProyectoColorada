from django.contrib import admin
from .models import (
    CompraInsumo, InventarioDiario, Empleado, Insumo,
    LineaPedido, BolsaPanFrio, LineaBolsaPanFrio, PedidoMayoreo, Producto,
    ProduccionDiaria, VentaSucursal,
)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "precio_publico", "precio_mayoreo", "stock_sucursal", "es_temporada", "activo")
    list_filter = ("activo", "es_temporada")
    search_fields = ("nombre",)
    list_editable = ("precio_publico", "precio_mayoreo", "activo")


@admin.register(Insumo)
class InsumoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "unidad", "activo")
    list_filter = ("unidad", "activo")
    search_fields = ("nombre",)
    list_editable = ("activo",)


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "rol", "usuario", "activo")
    list_filter = ("rol", "activo")
    search_fields = ("nombre",)


@admin.register(ProduccionDiaria)
class ProduccionDiariaAdmin(admin.ModelAdmin):
    list_display = ("fecha", "producto", "piezas_producidas")
    list_filter = ("fecha", "producto")
    date_hierarchy = "fecha"


@admin.register(CompraInsumo)
class CompraInsumoAdmin(admin.ModelAdmin):
    list_display = ("fecha", "insumo", "cantidad", "costo_total")
    list_filter = ("fecha", "insumo")
    date_hierarchy = "fecha"


@admin.register(VentaSucursal)
class VentaSucursalAdmin(admin.ModelAdmin):
    list_display = ("fecha", "empleado", "monto", "notas")
    list_filter = ("fecha", "empleado")
    date_hierarchy = "fecha"


class LineaPedidoInline(admin.TabularInline):
    model = LineaPedido
    extra = 1


@admin.register(PedidoMayoreo)
class PedidoMayoreoAdmin(admin.ModelAdmin):
    list_display = ("fecha", "empleado", "destino", "monto_recibido", "cerrado")
    list_filter = ("fecha", "empleado", "destino", "cerrado")
    inlines = [LineaPedidoInline]
    date_hierarchy = "fecha"


class LineaBolsaPanFrioInline(admin.TabularInline):
    model = LineaBolsaPanFrio
    extra = 1

@admin.register(BolsaPanFrio)
class BolsaPanFrioAdmin(admin.ModelAdmin):
    list_display = ("fecha_registro", "precio_remate", "vendido", "ingreso_generado", "cantidad_piezas")
    list_filter = ("vendido", "fecha_registro")
    inlines = [LineaBolsaPanFrioInline]
    date_hierarchy = "fecha_registro"

@admin.register(InventarioDiario)
class InventarioDiarioAdmin(admin.ModelAdmin):
    list_display = ("fecha", "producto", "conteo_apertura", "conteo_cierre")
    list_filter = ("fecha",)
    date_hierarchy = "fecha"