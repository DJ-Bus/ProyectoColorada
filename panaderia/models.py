# panaderia/models.py
from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils import timezone


# ─────────────────────────────────────────────
# MODELO BASE — timestamps de auditoría
# ─────────────────────────────────────────────

class ModeloBase(models.Model):
    """Clase abstracta que agrega timestamps a todos los modelos."""

    created_at = models.DateTimeField("Creado", auto_now_add=True)
    updated_at = models.DateTimeField("Actualizado", auto_now=True)

    class Meta:
        abstract = True


# ─────────────────────────────────────────────
# CATÁLOGOS
# ─────────────────────────────────────────────

class Insumo(ModeloBase):
    """Materia prima: Harina, Azúcar, Cocoa, Margarina… lo que sea."""

    UNIDADES = [
        ("bulto", "Bulto"),
        ("caja", "Caja"),
        ("kg", "Kilogramo"),
        ("g", "Gramo"),
        ("litro", "Litro"),
        ("pieza", "Pieza"),
    ]

    nombre = models.CharField(max_length=100)
    unidad = models.CharField(max_length=20, choices=UNIDADES)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Insumo"
        verbose_name_plural = "Insumos"
        ordering = ["nombre"]

    def __str__(self) -> str:
        return f"{self.nombre} ({self.get_unidad_display()})"


class Producto(ModeloBase):
    """Pan vendible: Concha, Coronada, Pan Mini… tu papá agrega los que quiera."""

    nombre = models.CharField(max_length=100)
    precio_publico = models.DecimalField(
        max_digits=8, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Precio en sucursal principal",
    )
    precio_mayoreo = models.DecimalField(
        max_digits=8, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Precio al que se le da a los puestos",
    )
    costo_produccion = models.DecimalField(
        max_digits=8, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Costo aproximado de hacer el pan",
        default=Decimal("6.00"),
    )
    stock_sucursal = models.PositiveIntegerField(default=0)
    es_temporada = models.BooleanField(
        default=False,
        help_text="Pan especial de temporada (Día de Muertos, Navidad…)",
    )
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ["nombre"]

    def __str__(self) -> str:
        return self.nombre

    def descontar_stock(self, cantidad: int) -> None:
        """Descuenta del mostrador validando que no quede negativo."""
        if cantidad > self.stock_sucursal:
            raise ValidationError(
                f"Stock insuficiente de '{self.nombre}'. "
                f"En mostrador: {self.stock_sucursal}, solicitado: {cantidad}."
            )
        self.stock_sucursal -= cantidad
        self.save(update_fields=["stock_sucursal"])

    def sumar_stock(self, cantidad: int) -> None:
        """Suma piezas al mostrador (producción, regreso de puesto)."""
        self.stock_sucursal += cantidad
        self.save(update_fields=["stock_sucursal"])


class Empleado(ModeloBase):
    """Persona que atiende la sucursal o lleva pan a un puesto."""

    ROLES = [
        ("sucursal", "Sucursal Principal"),
        ("puesto", "Puesto Mayoreo"),
    ]

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="empleado",
        help_text="Usuario de Django para login",
    )
    nombre = models.CharField(max_length=100)
    rol = models.CharField(max_length=20, choices=ROLES, default="sucursal")
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"
        ordering = ["nombre"]

    def __str__(self) -> str:
        return f"{self.nombre} ({self.get_rol_display()})"


# ─────────────────────────────────────────────
# OPERACIÓN DIARIA
# ─────────────────────────────────────────────

class ProduccionDiaria(ModeloBase):
    """
    Cuántas piezas salieron del horno hoy.
    Al guardar por primera vez, suma al stock_sucursal del producto.
    """

    fecha = models.DateField(default=timezone.now, db_index=True)
    producto = models.ForeignKey(
        Producto, on_delete=models.PROTECT, related_name="producciones"
    )
    piezas_producidas = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    class Meta:
        verbose_name = "Producción Diaria"
        verbose_name_plural = "Producción Diaria"
        ordering = ["-fecha"]
        constraints = [
            models.UniqueConstraint(
                fields=["fecha", "producto"],
                name="unique_produccion_diaria",
            )
        ]

    def save(self, *args, **kwargs) -> None:
        with transaction.atomic():
            if self.pk is None:
                Producto.objects.filter(pk=self.producto_id).update(
                    stock_sucursal=models.F("stock_sucursal") + self.piezas_producidas
                )
            super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.producto} — {self.piezas_producidas} pzs ({self.fecha:%d/%m/%Y})"


class CompraInsumo(ModeloBase):
    """Lo que se compró hoy en el mercado."""

    fecha = models.DateField(default=timezone.now, db_index=True)
    insumo = models.ForeignKey(
        Insumo, on_delete=models.PROTECT, related_name="compras"
    )
    cantidad = models.DecimalField(
        max_digits=8, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Cuántos bultos / cajas / kg se compraron",
    )
    costo_total = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Cuánto se pagó en total por esa compra",
    )

    class Meta:
        verbose_name = "Compra de Insumo"
        verbose_name_plural = "Compras de Insumos"
        ordering = ["-fecha"]

    @property
    def costo_unitario(self) -> Decimal:
        return self.costo_total / self.cantidad

    def __str__(self) -> str:
        return f"{self.insumo} — {self.cantidad} unidades (${self.costo_total})"


# ─────────────────────────────────────────────
# VENTAS Y CONSUMO INTERNO
# ─────────────────────────────────────────────

class ConsumoInterno(ModeloBase):
    """
    Pan tomado para consumo propio de la familia o empleados (ej. desayuno).
    Descuenta automáticamente del stock en mostrador.
    """
    fecha = models.DateField(default=timezone.now, db_index=True)
    producto = models.ForeignKey(
        Producto, on_delete=models.PROTECT, related_name="consumos_internos"
    )
    cantidad = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    motivo = models.CharField(
        max_length=200, blank=True, default="",
        help_text="Ej. Desayuno familiar, almuerzo empleados"
    )
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="consumos_internos_registrados"
    )

    class Meta:
        verbose_name = "Consumo Interno"
        verbose_name_plural = "Consumos Internos"
        ordering = ["-fecha", "-created_at"]

    def save(self, *args, **kwargs) -> None:
        with transaction.atomic():
            if self.pk is None:
                # Descontar del stock al registrar
                producto = Producto.objects.select_for_update().get(pk=self.producto_id)
                producto.descontar_stock(self.cantidad)
            super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.cantidad} x {self.producto.nombre} ({self.fecha:%d/%m/%Y}) - {self.motivo}"


class VentaSucursal(ModeloBase):
    """
    Registro de caja en mostrador.
    El empleado solo captura el monto cobrado al cliente — sin contar piezas.
    """

    empleado = models.ForeignKey(
        Empleado, on_delete=models.PROTECT, related_name="ventas_sucursal"
    )
    monto = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    fecha = models.DateTimeField(default=timezone.now, db_index=True)
    notas = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "Venta Sucursal"
        verbose_name_plural = "Ventas Sucursal"
        ordering = ["-fecha"]

    def __str__(self) -> str:
        return f"{self.empleado} — ${self.monto} ({self.fecha:%d/%m/%Y %H:%M})"


# ─────────────────────────────────────────────
# MAYOREO — Pedido con múltiples productos
# ─────────────────────────────────────────────

class PedidoMayoreo(ModeloBase):
    """
    Pedido que sale a un puesto por la mañana.
    Contiene múltiples líneas (productos).
    Al cerrar, el pan regresado se suma al stock de sucursal.
    """

    DESTINOS = [
        ("mercado", "Mercado"),
        ("la_burgos", "La Burgos"),
    ]

    empleado = models.ForeignKey(
        Empleado, on_delete=models.PROTECT, related_name="pedidos_mayoreo"
    )
    fecha = models.DateField(default=timezone.now, db_index=True)
    destino = models.CharField(
        max_length=30, choices=DESTINOS, default="mercado",
        help_text="¿A dónde se lleva el pan?",
    )
    monto_recibido = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"),
        help_text="Dinero que entregó el empleado al ajustar cuentas",
    )
    cerrado = models.BooleanField(
        default=False,
        help_text="¿Ya se hizo el ajuste de cuentas al final del día?",
    )

    class Meta:
        verbose_name = "Pedido Mayoreo"
        verbose_name_plural = "Pedidos Mayoreo"
        ordering = ["-fecha"]

    @property
    def total_piezas_entregadas(self) -> int:
        return sum(l.cantidad_entregada for l in self.lineas.all())

    @property
    def total_piezas_regresadas(self) -> int:
        return sum(l.cantidad_regresada for l in self.lineas.all())

    @property
    def total_piezas_vendidas(self) -> int:
        return self.total_piezas_entregadas - self.total_piezas_regresadas

    @property
    def total_esperado(self) -> Decimal:
        """Lo que debería entregar según precio mayoreo de cada línea."""
        return sum(
            (Decimal(l.cantidad_entregada - l.cantidad_regresada) * l.producto.precio_mayoreo)
            for l in self.lineas.select_related("producto")
        )

    @property
    def diferencia(self) -> Decimal:
        """Positivo = falta dinero. Negativo = sobra."""
        return self.total_esperado - self.monto_recibido

    def __str__(self) -> str:
        return (
            f"Pedido {self.empleado} → {self.get_destino_display()} "
            f"({self.fecha:%d/%m/%Y})"
        )


class LineaPedido(ModeloBase):
    """
    Línea de un pedido mayoreo: un producto con su cantidad.
    """

    pedido = models.ForeignKey(
        PedidoMayoreo, on_delete=models.CASCADE, related_name="lineas"
    )
    producto = models.ForeignKey(
        Producto, on_delete=models.PROTECT, related_name="lineas_pedido"
    )
    cantidad_entregada = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Piezas que se llevó",
    )
    cantidad_regresada = models.PositiveIntegerField(
        default=0,
        help_text="Piezas que devolvió al final del día",
    )
    prestado_de_sucursal = models.PositiveIntegerField(
        default=0,
        help_text="Piezas tomadas del mostrador",
    )

    class Meta:
        verbose_name = "Línea de Pedido"
        verbose_name_plural = "Líneas de Pedido"

    @property
    def piezas_vendidas(self) -> int:
        return self.cantidad_entregada - self.cantidad_regresada

    @property
    def subtotal_esperado(self) -> Decimal:
        return Decimal(self.piezas_vendidas) * self.producto.precio_mayoreo

    def clean(self) -> None:
        if self.cantidad_regresada > self.cantidad_entregada:
            raise ValidationError("No puede regresar más pan del que se llevó.")

    def __str__(self) -> str:
        return f"{self.producto} × {self.cantidad_entregada}"


# ─────────────────────────────────────────────
# CONTEO DE FIN DE DÍA
# ─────────────────────────────────────────────

class InventarioDiario(ModeloBase):
    """
    Control estricto de inventario por día.
    Apertura: Pan contado en la mañana.
    Cierre: Pan contado al final del día.
    """

    fecha = models.DateField(default=timezone.now, db_index=True)
    producto = models.ForeignKey(
        Producto, on_delete=models.PROTECT, related_name="inventarios_diarios"
    )
    conteo_apertura = models.PositiveIntegerField(
        default=0,
        help_text="Pan inicial en la mañana",
    )
    conteo_cierre = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Pan sobrante en la noche",
    )

    class Meta:
        verbose_name = "Inventario Diario"
        verbose_name_plural = "Inventarios Diarios"
        ordering = ["-fecha"]
        constraints = [
            models.UniqueConstraint(
                fields=["fecha", "producto"],
                name="unique_inventario_diario",
            )
        ]

    def __str__(self) -> str:
        cierre_str = self.conteo_cierre if self.conteo_cierre is not None else "?"
        return f"{self.producto} — Apertura: {self.conteo_apertura} Cierre: {cierre_str} ({self.fecha:%d/%m/%Y})"


# ─────────────────────────────────────────────
# PAN FRÍO (BOLSAS MIXTAS)
# ─────────────────────────────────────────────

class BolsaPanFrio(ModeloBase):
    """
    Bolsa mixta armada con pan sobrante del día anterior.
    """

    fecha_registro = models.DateField(default=timezone.now, db_index=True)
    precio_remate = models.DecimalField(
        max_digits=8, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Precio total de la bolsa armada",
    )
    vendido = models.BooleanField(
        default=False,
        help_text="¿Ya se vendió esta bolsa?",
    )
    ingreso_generado = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"),
        help_text="Dinero que entró al vender la bolsa",
    )

    class Meta:
        verbose_name = "Bolsa de Pan Frío"
        verbose_name_plural = "Bolsas de Pan Frío"
        ordering = ["-fecha_registro"]

    @property
    def cantidad_piezas(self) -> int:
        return sum(l.cantidad for l in self.lineas.all())

    def __str__(self) -> str:
        estado = "Vendido" if self.vendido else "Disponible"
        return f"Bolsa Pan Frío — {self.fecha_registro:%d/%m/%Y} [{estado}]"


class LineaBolsaPanFrio(ModeloBase):
    """
    Pan contenido dentro de una bolsa de pan frío.
    """

    bolsa = models.ForeignKey(
        BolsaPanFrio, on_delete=models.CASCADE, related_name="lineas"
    )
    producto = models.ForeignKey(
        Producto, on_delete=models.PROTECT, related_name="lineas_pan_frio"
    )
    cantidad = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Piezas de este producto ingresadas en la bolsa",
    )

    class Meta:
        verbose_name = "Línea de Bolsa Fría"
        verbose_name_plural = "Líneas de Bolsa Fría"

    def __str__(self) -> str:
        return f"{self.cantidad} × {self.producto}"