# models.py
from __future__ import annotations
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils import timezone


# ─────────────────────────────────────────────
# CATÁLOGOS (Tu papá los administra)
# ─────────────────────────────────────────────

class Insumo(models.Model):
    """Materia prima: Harina, Azúcar, Cocoa, Margarina… lo que sea."""

    UNIDADES = [
        ("bulto", "Bulto"),
        ("caja", "Caja"),
        ("kg", "Kilogramo"),
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


class Producto(models.Model):
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
    # Stock en sucursal: se llena con ProduccionDiaria y baja con préstamos
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


class Empleado(models.Model):
    """Persona que atiende la sucursal o lleva pan a un puesto."""

    ROLES = [
        ("sucursal", "Sucursal Principal"),
        ("puesto", "Puesto Mayoreo"),
    ]

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

class ProduccionDiaria(models.Model):
    """
    Cuántas piezas salieron del horno hoy.
    Al guardar, suma al stock_sucursal del producto.
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
        # Un registro por producto por día
        unique_together = [("fecha", "producto")]

    def save(self, *args, **kwargs) -> None:
        with transaction.atomic():
            if self.pk is None:
                # Primera vez: suma al mostrador
                Producto.objects.filter(pk=self.producto_id).update(
                    stock_sucursal=models.F("stock_sucursal") + self.piezas_producidas
                )
            super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.producto} — {self.piezas_producidas} pzs ({self.fecha:%d/%m/%Y})"


class CompraInsumo(models.Model):
    """
    Lo que se compró hoy en el mercado.
    No se lleva control de precio fijo — varía diario, se registra al comprar.
    """

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
# VENTAS
# ─────────────────────────────────────────────

class VentaSucursal(models.Model):
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


class PedidoMayoreo(models.Model):
    """
    Pan que sale a un puesto por la mañana y se ajusta al regresar.

    Flujo:
      1. Se crea con cantidad_entregada (producción + préstamo de sucursal).
      2. Al regresar, se actualiza cantidad_regresada.
      3. El sistema calcula piezas_vendidas y total_a_pagar.

    El campo prestado_de_sucursal descuenta automáticamente el stock
    del mostrador en el momento de la creación (con transacción atómica).
    """

    empleado = models.ForeignKey(
        Empleado, on_delete=models.PROTECT, related_name="pedidos_mayoreo"
    )
    producto = models.ForeignKey(
        Producto, on_delete=models.PROTECT, related_name="pedidos_mayoreo"
    )
    fecha = models.DateField(default=timezone.now, db_index=True)
    cantidad_entregada = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Total de piezas que se llevó (producción + préstamo)",
    )
    cantidad_regresada = models.PositiveIntegerField(
        default=0,
        help_text="Pan que devolvió al final del día",
    )
    prestado_de_sucursal = models.PositiveIntegerField(
        default=0,
        help_text="Piezas tomadas del mostrador para completar el pedido",
    )
    monto_recibido = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"),
        help_text="Dinero que entregó el empleado al ajustar cuentas",
    )

    class Meta:
        verbose_name = "Pedido Mayoreo"
        verbose_name_plural = "Pedidos Mayoreo"
        ordering = ["-fecha"]

    # ── Propiedades calculadas ──────────────────

    @property
    def piezas_vendidas(self) -> int:
        return self.cantidad_entregada - self.cantidad_regresada

    @property
    def total_esperado(self) -> Decimal:
        """Lo que debería entregar según precio mayoreo."""
        return Decimal(self.piezas_vendidas) * self.producto.precio_mayoreo

    @property
    def diferencia(self) -> Decimal:
        """Positivo = falta dinero. Negativo = sobra (raro pero posible)."""
        return self.total_esperado - self.monto_recibido

    # ── Validación ──────────────────────────────

    def clean(self) -> None:
        if self.cantidad_regresada > self.cantidad_entregada:
            raise ValidationError(
                "No puede regresar más pan del que se llevó."
            )

    # ── Persistencia ────────────────────────────

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        if self.pk is None and self.prestado_de_sucursal > 0:
            with transaction.atomic():
                producto = Producto.objects.select_for_update().get(
                    pk=self.producto_id
                )
                producto.descontar_stock(self.prestado_de_sucursal)
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)

    def __str__(self) -> str:
        return (
            f"Pedido {self.empleado} — {self.producto} "
            f"({self.cantidad_entregada} pzs, {self.fecha:%d/%m/%Y})"
        )


# ─────────────────────────────────────────────
# PAN FRÍO
# ─────────────────────────────────────────────

class PanFrio(models.Model):
    """
    Lote de pan sobrante acumulado para remate.
    Origen: lo que regresaron los puestos + lo que no se vendió en sucursal.
    Se vende más barato como lote o bolsa.
    """

    fecha_registro = models.DateField(default=timezone.now, db_index=True)
    cantidad_piezas = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Total de pan sobrante reunido ese día",
    )
    precio_remate = models.DecimalField(
        max_digits=8, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Precio por bolsa/lote de pan frío",
    )
    vendido = models.BooleanField(
        default=False,
        help_text="¿Ya se vendió este lote?",
    )
    ingreso_generado = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"),
        help_text="Dinero real que entró al vender el pan frío",
    )

    class Meta:
        verbose_name = "Pan Frío"
        verbose_name_plural = "Pan Frío"
        ordering = ["-fecha_registro"]

    def __str__(self) -> str:
        estado = "Vendido" if self.vendido else "Disponible"
        return (
            f"Lote Pan Frío — {self.fecha_registro:%d/%m/%Y} "
            f"({self.cantidad_piezas} pzs) [{estado}]"
        )