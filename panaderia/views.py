from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .decorators import staff_required
from .models import (
    CompraInsumo,
    InventarioDiario,
    Empleado,
    Insumo,
    LineaPedido,
    BolsaPanFrio,
    LineaBolsaPanFrio,
    PedidoMayoreo,
    Producto,
    ProduccionDiaria,
    VentaSucursal,
)
from .services import calcular_corte_dia


# ─────────────────────────────────────────────
# VENTAS
# ─────────────────────────────────────────────

@login_required
def registrar_venta(request):
    """Pantalla del empleado para registrar ventas en el mostrador."""
    hoy = timezone.now().date()

    if request.method == "POST":
        monto = request.POST.get("monto")
        notas = request.POST.get("notas", "")
        try:
            empleado = request.user.empleado
        except Empleado.DoesNotExist:
            messages.error(request, "Tu usuario no tiene un empleado asociado. Contacta al administrador.")
            return redirect("panaderia:registrar_venta")

        try:
            monto_decimal = Decimal(monto)
            if monto_decimal <= 0:
                raise ValueError
            VentaSucursal.objects.create(empleado=empleado, monto=monto_decimal, notas=notas)
            messages.success(request, f"✅ Venta de ${monto_decimal} registrada.")
        except (InvalidOperation, ValueError, TypeError):
            messages.error(request, "Ingresa un monto válido.")
        return redirect("panaderia:registrar_venta")

    ultimas_ventas = VentaSucursal.objects.filter(fecha__date=hoy).order_by("-fecha")[:10]

    return render(request, "ventas/registrar.html", {
        "ultimas_ventas": ultimas_ventas,
    })


@login_required
@staff_required
def corte_del_dia(request):
    """Resumen financiero del día — solo para el dueño (staff)."""
    fecha_str = request.GET.get("fecha")
    if fecha_str:
        try:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            fecha = timezone.now().date()
    else:
        fecha = timezone.now().date()

    totales = calcular_corte_dia(fecha)
    ventas_sucursal = VentaSucursal.objects.filter(fecha__date=fecha).order_by("-fecha")
    pedidos_mayoreo = PedidoMayoreo.objects.filter(fecha=fecha).select_related("empleado").prefetch_related("lineas__producto")
    compras = CompraInsumo.objects.filter(fecha=fecha).select_related("insumo")

    return render(request, "ventas/corte.html", {
        "fecha": fecha,
        "totales": totales,
        "ventas_sucursal": ventas_sucursal,
        "pedidos_mayoreo": pedidos_mayoreo,
        "compras": compras,
    })


# ─────────────────────────────────────────────
# PRODUCCIÓN
# ─────────────────────────────────────────────

@login_required
@staff_required
def registrar_produccion(request):
    """Registrar cuántas piezas salieron del horno hoy."""
    hoy = timezone.now().date()

    if request.method == "POST":
        action = request.POST.get("action", "produccion")

        if action == "nuevo_producto":
            # Crear nuevo producto desde esta pantalla
            nombre = request.POST.get("nuevo_nombre", "").strip()
            precio_pub = request.POST.get("nuevo_precio_publico")
            precio_may = request.POST.get("nuevo_precio_mayoreo")
            if nombre and precio_pub and precio_may:
                try:
                    Producto.objects.create(
                        nombre=nombre,
                        precio_publico=Decimal(precio_pub),
                        precio_mayoreo=Decimal(precio_may),
                    )
                    messages.success(request, f"🍞 Producto '{nombre}' creado.")
                except Exception as e:
                    messages.error(request, f"Error al crear producto: {e}")
            else:
                messages.error(request, "Completa todos los campos del nuevo producto.")
            return redirect("panaderia:registrar_produccion")

        # Registrar producción
        producto_id = request.POST.get("producto")
        piezas = request.POST.get("piezas_producidas")
        if producto_id and piezas:
            try:
                ProduccionDiaria.objects.create(
                    producto_id=int(producto_id),
                    piezas_producidas=int(piezas),
                )
                messages.success(request, "🔥 Producción registrada. Stock actualizado.")
            except Exception as e:
                messages.error(request, f"Error: {e}")
        return redirect("panaderia:registrar_produccion")

    productos = Producto.objects.filter(activo=True)
    produccion_hoy = ProduccionDiaria.objects.filter(fecha=hoy).select_related("producto")
    total_piezas_hoy = produccion_hoy.aggregate(total=Sum("piezas_producidas"))["total"] or 0

    return render(request, "produccion/registrar.html", {
        "productos": productos,
        "produccion_hoy": produccion_hoy,
        "total_piezas_hoy": total_piezas_hoy,
    })


@login_required
@staff_required
def ver_stock(request):
    """Ver inventario actual en sucursal."""
    productos = Producto.objects.filter(activo=True)
    return render(request, "produccion/stock.html", {
        "productos": productos,
    })


@login_required
@staff_required
def conteo_sucursal(request):
    """Conteo de pan al inicio y final del día en sucursal."""
    hoy = timezone.now().date()

    if request.method == "POST":
        tipo_conteo = request.POST.get("tipo_conteo") # Puede ser "apertura" o "cierre"
        
        try:
            with transaction.atomic():
                productos = Producto.objects.filter(activo=True)
                for producto in productos:
                    cantidad = request.POST.get(f"conteo_{producto.id}")
                    if cantidad and cantidad.strip():
                        inv, created = InventarioDiario.objects.get_or_create(
                            fecha=hoy, producto=producto
                        )
                        if tipo_conteo == "apertura":
                            inv.conteo_apertura = int(cantidad)
                        elif tipo_conteo == "cierre":
                            inv.conteo_cierre = int(cantidad)
                        inv.save()
                        
            messages.success(request, f"📋 Conteo de {tipo_conteo} guardado correctamente.")
        except Exception as e:
            messages.error(request, f"Ocurrió un error guardando el conteo: {e}")
            
        return redirect("panaderia:conteo_sucursal")

    productos = Producto.objects.filter(activo=True)
    conteos_hoy = {
        inv.producto_id: inv
        for inv in InventarioDiario.objects.filter(fecha=hoy)
    }

    productos_con_conteo = []
    for p in productos:
        inv = conteos_hoy.get(p.id)
        productos_con_conteo.append({
            "producto": p,
            "apertura": inv.conteo_apertura if inv else "",
            "cierre": inv.conteo_cierre if inv and inv.conteo_cierre is not None else "",
        })

    return render(request, "produccion/conteo.html", {
        "productos_con_conteo": productos_con_conteo,
        "hoy": hoy,
    })


@login_required
@staff_required
def tablero_inventario(request):
    """Tablero general de inventario: Apertura + Producción + Regresos - Cierre = Vendido."""
    hoy = timezone.now().date()
    
    productos = Producto.objects.filter(activo=True)
    
    # Obtener inventario diario
    inventarios = {inv.producto_id: inv for inv in InventarioDiario.objects.filter(fecha=hoy)}
    
    # Obtener producción
    produccion = ProduccionDiaria.objects.filter(fecha=hoy).values('producto_id').annotate(total=Sum('piezas_producidas'))
    prod_dict = {p['producto_id']: p['total'] for p in produccion}
    
    # Obtener regresos de mayoreo
    lineas_regreso = LineaPedido.objects.filter(pedido__fecha=hoy).values('producto_id').annotate(total=Sum('cantidad_regresada'))
    regresos_dict = {l['producto_id']: l['total'] for l in lineas_regreso}
    
    # Obtener entregados a mayoreo (para sacarlo del disponible esperado en mostrador)
    lineas_entregado = LineaPedido.objects.filter(pedido__fecha=hoy).values('producto_id').annotate(total=Sum('cantidad_entregada'))
    entregado_dict = {l['producto_id']: l['total'] for l in lineas_entregado}
    
    # Obtener bolsas de pan frío (pan que se armó en bolsa hoy, asumiendo que cuenta como merma o salida)
    # Por ahora solo lo mostraremos como informativo o sumado a las salidas.
    lineas_bolsas = LineaBolsaPanFrio.objects.filter(bolsa__fecha_registro=hoy).values('producto_id').annotate(total=Sum('cantidad'))
    bolsas_dict = {b['producto_id']: b['total'] for b in lineas_bolsas}

    tablero_data = []
    
    for p in productos:
        inv = inventarios.get(p.id)
        apertura = inv.conteo_apertura if inv else 0
        cierre = inv.conteo_cierre if inv and inv.conteo_cierre is not None else 0
        
        producido = prod_dict.get(p.id, 0)
        regresado = regresos_dict.get(p.id, 0)
        entregado = entregado_dict.get(p.id, 0)
        en_bolsas_frio = bolsas_dict.get(p.id, 0)
        
        # Apertura + Producción - Entregado a mayoreo + Regresado de mayoreo - En Bolsas = Disponible esperado
        # Vendido = Disponible esperado - Cierre
        disponible_esperado = apertura + producido - entregado + regresado - en_bolsas_frio
        vendido_calculado = disponible_esperado - cierre
        if vendido_calculado < 0:
            vendido_calculado = 0  # Prevenir negativos si el cierre es mayor al esperado
            
        tablero_data.append({
            "producto": p,
            "apertura": apertura,
            "producido": producido,
            "entregado": entregado,
            "regresado": regresado,
            "bolsas_frio": en_bolsas_frio,
            "cierre": cierre if inv and inv.conteo_cierre is not None else "?",
            "vendido_calculado": vendido_calculado if (inv and inv.conteo_cierre is not None) else "?"
        })
        
    return render(request, "produccion/tablero.html", {
        "tablero_data": tablero_data,
        "hoy": hoy,
    })

# ─────────────────────────────────────────────
# COMPRAS
# ─────────────────────────────────────────────

@login_required
@staff_required
def registrar_compra(request):
    """Registrar compra de insumos del mercado."""
    hoy = timezone.now().date()

    if request.method == "POST":
        action = request.POST.get("action", "compra")

        if action == "nuevo_insumo":
            nombre = request.POST.get("nuevo_nombre", "").strip()
            unidad = request.POST.get("nuevo_unidad")
            if nombre and unidad:
                try:
                    Insumo.objects.create(nombre=nombre, unidad=unidad)
                    messages.success(request, f"✅ Insumo '{nombre}' creado.")
                except Exception as e:
                    messages.error(request, f"Error: {e}")
            else:
                messages.error(request, "Completa nombre y unidad del insumo.")
            return redirect("panaderia:registrar_compra")

        # Registrar compra
        insumo_id = request.POST.get("insumo")
        cantidad = request.POST.get("cantidad")
        costo_total = request.POST.get("costo_total")
        if insumo_id and cantidad and costo_total:
            try:
                CompraInsumo.objects.create(
                    insumo_id=int(insumo_id),
                    cantidad=Decimal(cantidad),
                    costo_total=Decimal(costo_total),
                )
                messages.success(request, "🛒 Compra registrada correctamente.")
            except Exception as e:
                messages.error(request, f"Error: {e}")
        return redirect("panaderia:registrar_compra")

    insumos = Insumo.objects.filter(activo=True)
    compras_hoy = CompraInsumo.objects.filter(fecha=hoy).select_related("insumo")
    total_compras_hoy = compras_hoy.aggregate(total=Sum("costo_total"))["total"] or Decimal("0.00")

    return render(request, "compras/registrar.html", {
        "insumos": insumos,
        "unidades_choices": Insumo.UNIDADES,
        "compras_hoy": compras_hoy,
        "total_compras_hoy": total_compras_hoy,
    })


# ─────────────────────────────────────────────
# MAYOREO
# ─────────────────────────────────────────────

@login_required
@staff_required
def crear_pedido(request):
    """
    Crear pedido mayoreo multi-producto.
    Paso 1: Se cargan líneas (producto + cantidad) en una tabla.
    Paso 2: Se envía todo junto para crear el pedido.
    """
    if request.method == "POST":
        empleado_id = request.POST.get("empleado")
        destino = request.POST.get("destino")
        productos_ids = request.POST.getlist("producto_id[]")
        cantidades = request.POST.getlist("cantidad[]")
        prestamos = request.POST.getlist("prestado[]")

        if not empleado_id or not destino or not productos_ids:
            messages.error(request, "Completa todos los campos y agrega al menos un producto.")
            return redirect("panaderia:crear_pedido")

        try:
            with transaction.atomic():
                pedido = PedidoMayoreo.objects.create(
                    empleado_id=int(empleado_id),
                    destino=destino,
                )

                for i, prod_id in enumerate(productos_ids):
                    cant = int(cantidades[i]) if i < len(cantidades) else 0
                    prest = int(prestamos[i]) if i < len(prestamos) else 0

                    if cant <= 0:
                        continue

                    linea = LineaPedido.objects.create(
                        pedido=pedido,
                        producto_id=int(prod_id),
                        cantidad_entregada=cant,
                        prestado_de_sucursal=prest,
                    )

                    # Descontar préstamo del stock de sucursal
                    if prest > 0:
                        producto = Producto.objects.select_for_update().get(pk=int(prod_id))
                        producto.descontar_stock(prest)

                messages.success(request, f"🚚 Pedido creado con {len(productos_ids)} productos.")
        except Exception as e:
            messages.error(request, f"Error al crear pedido: {e}")

        return redirect("panaderia:lista_pedidos")

    empleados_puesto = Empleado.objects.filter(rol="puesto", activo=True)
    productos = Producto.objects.filter(activo=True)

    return render(request, "mayoreo/crear_pedido.html", {
        "empleados_puesto": empleados_puesto,
        "productos": productos,
        "destinos": PedidoMayoreo.DESTINOS,
    })


@login_required
@staff_required
def cerrar_pedido(request, pedido_id):
    """Cerrar un pedido mayoreo — ajuste de cuentas al regresar del puesto."""
    pedido = get_object_or_404(
        PedidoMayoreo.objects.prefetch_related("lineas__producto"),
        pk=pedido_id,
    )

    if pedido.cerrado:
        messages.warning(request, "Este pedido ya fue cerrado.")
        return redirect("panaderia:lista_pedidos")

    if request.method == "POST":
        monto_recibido = request.POST.get("monto_recibido", "0")

        try:
            with transaction.atomic():
                # Actualizar cada línea con la cantidad regresada
                for linea in pedido.lineas.all():
                    regresada = request.POST.get(f"regresada_{linea.id}", "0")
                    linea.cantidad_regresada = int(regresada)
                    linea.save()

                    # Sumar el pan regresado al stock de sucursal
                    if linea.cantidad_regresada > 0:
                        producto = Producto.objects.select_for_update().get(pk=linea.producto_id)
                        producto.sumar_stock(linea.cantidad_regresada)

                pedido.monto_recibido = Decimal(monto_recibido)
                pedido.cerrado = True
                pedido.save()

                diff = pedido.diferencia
                if diff > 0:
                    messages.warning(request, f"⚠️ Pedido cerrado. Falta dinero: ${diff:.2f}")
                elif diff < 0:
                    messages.info(request, f"ℹ️ Pedido cerrado. Sobra dinero: ${abs(diff):.2f}")
                else:
                    messages.success(request, "✅ Pedido cerrado. Cuentas al corriente.")
        except Exception as e:
            messages.error(request, f"Error al cerrar pedido: {e}")

        return redirect("panaderia:lista_pedidos")

    return render(request, "mayoreo/cerrar_pedido.html", {
        "pedido": pedido,
    })


@login_required
@staff_required
def lista_pedidos(request):
    """Lista de pedidos mayoreo del día."""
    hoy = timezone.now().date()
    pedidos = (
        PedidoMayoreo.objects
        .filter(fecha=hoy)
        .select_related("empleado")
        .prefetch_related("lineas__producto")
        .order_by("-created_at")
    )
    return render(request, "mayoreo/lista.html", {
        "pedidos": pedidos,
        "hoy": hoy,
    })


# ─────────────────────────────────────────────
# PAN FRÍO
# ─────────────────────────────────────────────

@login_required
@staff_required
def pan_frio_lista(request):
    """Gestión de lotes de pan frío — crear bolsas mixtas y marcar como vendido."""
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "crear":
            precio = request.POST.get("precio_remate")
            productos_ids = request.POST.getlist("producto_id[]")
            cantidades = request.POST.getlist("cantidad[]")
            
            if not precio or not productos_ids:
                messages.error(request, "Añade un precio y al menos un producto a la bolsa.")
                return redirect("panaderia:pan_frio_lista")
                
            try:
                with transaction.atomic():
                    bolsa = BolsaPanFrio.objects.create(
                        precio_remate=Decimal(precio)
                    )
                    
                    for i, prod_id in enumerate(productos_ids):
                        cant = int(cantidades[i]) if i < len(cantidades) else 0
                        if cant <= 0:
                            continue
                            
                        LineaBolsaPanFrio.objects.create(
                            bolsa=bolsa,
                            producto_id=int(prod_id),
                            cantidad=cant,
                        )
                        
                        # Descontar del stock directamente (son panes sobrantes que ya están físicamente apartados)
                        producto = Producto.objects.select_for_update().get(pk=int(prod_id))
                        producto.descontar_stock(cant)
                        
                    messages.success(request, f"🧊 Bolsa de pan frío creada con {len(productos_ids)} panes distintos.")
            except Exception as e:
                messages.error(request, f"Error al crear bolsa: {e}")

        elif action == "vender":
            lote_id = request.POST.get("lote_id")
            ingreso = request.POST.get("ingreso_generado")
            try:
                bolsa = BolsaPanFrio.objects.get(pk=lote_id, vendido=False)
                bolsa.vendido = True
                bolsa.ingreso_generado = Decimal(ingreso)
                bolsa.save()
                messages.success(request, f"✅ Bolsa vendida por ${bolsa.ingreso_generado}")
            except BolsaPanFrio.DoesNotExist:
                messages.error(request, "Bolsa no encontrada o ya vendida.")
            except (InvalidOperation, TypeError):
                messages.error(request, "Ingresa un monto válido.")

        return redirect("panaderia:pan_frio_lista")

    productos = Producto.objects.filter(activo=True)
    bolsas = BolsaPanFrio.objects.prefetch_related('lineas__producto').all()[:20]

    return render(request, "pan_frio/lista.html", {
        "productos": productos,
        "bolsas": bolsas,
    })