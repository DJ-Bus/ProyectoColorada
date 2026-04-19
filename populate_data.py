import os
import django
from decimal import Decimal
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from panaderia.models import (
    Insumo, Producto, Empleado, ProduccionDiaria, CompraInsumo,
    VentaSucursal, PedidoMayoreo, LineaPedido, InventarioDiario,
    BolsaPanFrio, LineaBolsaPanFrio
)

def run():
    print("Borrando datos existentes...")
    LineaBolsaPanFrio.objects.all().delete()
    BolsaPanFrio.objects.all().delete()
    InventarioDiario.objects.all().delete()
    LineaPedido.objects.all().delete()
    PedidoMayoreo.objects.all().delete()
    VentaSucursal.objects.all().delete()
    CompraInsumo.objects.all().delete()
    ProduccionDiaria.objects.all().delete()
    Producto.objects.all().delete()
    Insumo.objects.all().delete()
    Empleado.objects.all().delete()

    print("Creando insumos...")
    nombres_insumos = [
        "Harina", "Huevo", "Azúcar", "Levadura", "Chocolate",
        "Vainilla", "Manteca", "Margarina", "Sal"
    ]
    for n in nombres_insumos:
        # Defaulting to kilogramo for solid, but we don't have enough detail, so let's put 'kg' or 'pieza'
        unidad = "kg"
        if n in ["Vainilla", "Huevo"]:
            unidad = "litro" if n == "Vainilla" else "pieza"
        Insumo.objects.create(nombre=n, unidad=unidad)

    print("Creando empleado Casasano...")
    empleado_casasano = Empleado.objects.create(
        nombre="Empleado Casasano",
        rol="puesto"
    )

    productos_info = {
        # nombre: (costo, publico, mayoreo)
        "Conchas": (6, 10, 4),
        "Rebanadas": (6, 10, 4),
        "Roscas mecas": (6, 10, 8),
        "Cemitas": (6, 10, 4),
        "Yoyos": (6, 10, 4),
        "Apasteladas": (6, 10, 4),
        "Chamucos": (6, 10, 4),
        "Gusanos": (6, 10, 8),
        "Coronadas": (6, 10, 4),
        "Granadas": (6, 10, 4),
        "Esferas": (6, 10, 4),
        "Volcanes": (6, 10, 4),
        "Cuernos chilapeños": (6, 10, 4),
        "Rodillas": (6, 10, 4),
        "Capotes": (6, 10, 4),
        "Huesos": (6, 10, 4),
        "Roscas de manteca": (6, 10, 4),
        "Bisquets": (6, 10, 4),
        "Cuernos Daneses": (6, 10, 4),
        "Chinos": (6, 12, 9),
        "Nidos": (6, 12, 9),
        "Rollos de piña": (6, 12, 9),
        "Cubiletes": (6, 12, 9),
        "Donas de chocolate": (6, 12, 9),
        "Cortados de piloncillo": (6, 12, 9),
        "Empanochadas": (6, 18, 12),
        "Bolillos": (2, 3, 3),
        "Teleras": (2, 3, 3),
        "Pan mini variado": (4, 6, 4),
        "Hojaldras": (6, 10, 4),
        "Borrachos": (6, 10, 4),
        "Empanadas": (6, 10, 4),
        "Bigotes": (6, 10, 4),
        "Mantecadas": (6, 10, 4),
    }

    piezas = {
        "Conchas": 12, "Rebanadas": 11, "Roscas mecas": 6, "Cemitas": 4, "Yoyos": 6,
        "Apasteladas": 7, "Chamucos": 11, "Gusanos": 8, "Coronadas": 5, "Granadas": 2,
        "Esferas": 3, "Volcanes": 5, "Cuernos chilapeños": 5, "Rodillas": 3, "Capotes": 2,
        "Huesos": 4, "Roscas de manteca": 4, "Bisquets": 3, "Cuernos Daneses": 5,
        "Chinos": 2, "Nidos": 3, "Rollos de piña": 8, "Cubiletes": 2, "Donas de chocolate": 4,
        "Cortados de piloncillo": 2, "Empanochadas": 2, "Bolillos": 20, "Teleras": 14, 
        "Pan mini variado": 60, "Mantecadas": 10,
    }

    produccion = {
        "Coronadas": 72, "Cuernos chilapeños": 12, "Volcanes": 12, "Esferas": 24,
        "Granadas": 24, "Huesos": 6, "Roscas de manteca": 6, "Bisquets": 12, "Cemitas": 12,
        "Gusanos": 23, "Conchas": 48, "Hojaldras": 6, "Capotes": 6, "Borrachos": 24,
        "Cuernos Daneses": 24, "Empanadas": 12, "Bigotes": 6, "Chinos": 22, "Nidos": 12,
        "Cubiletes": 12, "Donas de chocolate": 12, "Cortados de piloncillo": 8,
        "Empanochadas": 8, "Pan mini variado": 255,
    }

    pedido_casasano = {
        "Coronadas": 30, "Cuernos chilapeños": 4, "Volcanes": 4, "Granadas": 8, "Esferas": 8,
        "Huesos": 3, "Roscas de manteca": 3, "Cemitas": 4, "Bisquets": 4, "Empanadas": 6,
        "Bigotes": 4, "Mantecadas": 5, "Rebanadas": 5, "Borrachos": 10, "Cuernos Daneses": 10,
        "Apasteladas": 4, "Nidos": 6, "Chinos": 6, "Gusanos": 8, "Rollos de piña": 3,
        "Yoyos": 3, "Cortados de piloncillo": 2, "Empanochadas": 1, "Donas de chocolate": 6,
        "Chamucos": 4, "Cubiletes": 4, "Hojaldras": 4, "Capotes": 3, "Conchas": 20,
        "Pan mini variado": 50,
    }

    print("Creando productos con sus precios y stock inicial...")
    productos_obj = {}
    for nombre, (costo, publico, mayoreo) in productos_info.items():
        stock_inicial = piezas.get(nombre, 0)
        prod = Producto.objects.create(
            nombre=nombre,
            costo_produccion=Decimal(str(costo)),
            precio_publico=Decimal(str(publico)),
            precio_mayoreo=Decimal(str(mayoreo)),
            stock_sucursal=stock_inicial
        )
        productos_obj[nombre] = prod

    print("Registrando producción del día (esto sumará al stock)...")
    hoy = timezone.now().date()
    for nombre, cantidad in produccion.items():
        prod = productos_obj[nombre]
        # Al guardar ProduccionDiaria, se suma al stock de la sucursal automáticamente
        ProduccionDiaria.objects.create(
            fecha=hoy,
            producto=prod,
            piezas_producidas=cantidad
        )

    print("Generando pedido de Casasano y descontando stock...")
    pedido = PedidoMayoreo.objects.create(
        empleado=empleado_casasano,
        fecha=hoy,
        destino="mercado" # Or la_burgos, "mercado" is default
    )

    for nombre, cantidad in pedido_casasano.items():
        prod = productos_obj[nombre]
        # Refrescar para tener el stock actualizado después de la producción
        prod.refresh_from_db()
        # Verificar que alcance el stock, o descontar igual (asumiremos que hay stock porque así es la lista)
        if prod.stock_sucursal >= cantidad:
            prod.descontar_stock(cantidad)
        else:
            print(f"Warning: Stock insuficiente de {nombre} ({prod.stock_sucursal} vs {cantidad}), forzando descuento.")
            prod.stock_sucursal -= cantidad
            prod.save()

        LineaPedido.objects.create(
            pedido=pedido,
            producto=prod,
            cantidad_entregada=cantidad,
            cantidad_regresada=0
        )

    print("Listo! Datos poblados correctamente.")

if __name__ == "__main__":
    run()
