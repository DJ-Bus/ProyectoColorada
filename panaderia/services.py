"""
Servicios de lógica de negocio — separados de los modelos para Clean Code.
"""
from datetime import date
from decimal import Decimal

from django.db.models import Sum

from .models import CompraInsumo, PedidoMayoreo, VentaSucursal


def calcular_corte_dia(fecha: date) -> dict:
    """
    Calcula los totales del día para el corte de caja.

    Retorna un diccionario con:
        - ventas_sucursal: total de ventas en mostrador
        - cobro_mayoreo: total de dinero recibido de los puestos
        - gasto_insumos: total gastado en compras del mercado
        - ganancia_neta: ventas + mayoreo - compras
    """
    ventas_sucursal = (
        VentaSucursal.objects
        .filter(fecha__date=fecha)
        .aggregate(total=Sum("monto"))["total"]
        or Decimal("0.00")
    )

    cobro_mayoreo = (
        PedidoMayoreo.objects
        .filter(fecha=fecha)
        .aggregate(total=Sum("monto_recibido"))["total"]
        or Decimal("0.00")
    )

    gasto_insumos = (
        CompraInsumo.objects
        .filter(fecha=fecha)
        .aggregate(total=Sum("costo_total"))["total"]
        or Decimal("0.00")
    )

    ganancia_neta = ventas_sucursal + cobro_mayoreo - gasto_insumos

    return {
        "ventas_sucursal": ventas_sucursal,
        "cobro_mayoreo": cobro_mayoreo,
        "gasto_insumos": gasto_insumos,
        "ganancia_neta": ganancia_neta,
    }
