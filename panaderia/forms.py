from django import forms
from .models import (
    VentaSucursal, ProduccionDiaria, CompraInsumo,
    PedidoMayoreo, PanFrio,
)


class VentaSucursalForm(forms.ModelForm):
    class Meta:
        model = VentaSucursal
        fields = ["monto", "notas"]
        widgets = {
            "monto": forms.NumberInput(attrs={
                "inputmode": "decimal",
                "step": "0.01",
                "min": "0.01",
                "placeholder": "0.00",
                "class": "form-control form-control-lg",
            }),
            "notas": forms.Textarea(attrs={
                "rows": 2,
                "placeholder": "Ej: cliente frecuente, pan de encargo...",
                "class": "form-control",
            }),
        }


class ProduccionDiariaForm(forms.ModelForm):
    class Meta:
        model = ProduccionDiaria
        fields = ["producto", "piezas_producidas"]


class CompraInsumoForm(forms.ModelForm):
    class Meta:
        model = CompraInsumo
        fields = ["insumo", "cantidad", "costo_total"]


class PedidoMayoreoForm(forms.ModelForm):
    class Meta:
        model = PedidoMayoreo
        fields = ["empleado", "producto", "cantidad_entregada", "prestado_de_sucursal"]


class CerrarPedidoForm(forms.Form):
    cantidad_regresada = forms.IntegerField(min_value=0)
    monto_recibido = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0)


class PanFrioForm(forms.ModelForm):
    class Meta:
        model = PanFrio
        fields = ["producto", "cantidad_piezas", "precio_remate"]