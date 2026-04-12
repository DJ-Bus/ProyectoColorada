from django import forms
from .models import VentaSucursal, Empleado

class VentaSucursalForm(forms.ModelForm):
    class Meta:
        model = VentaSucursal
        fields = ['empleado', 'monto', 'notas']
        widgets = {
            'empleado': forms.Select(attrs={'class': 'w-full p-3 border rounded-lg bg-gray-50'}),
            'monto': forms.NumberInput(attrs={'class': 'w-full p-3 border rounded-lg bg-gray-50', 'placeholder': 'Ej. 150.50'}),
            'notas': forms.Textarea(attrs={'class': 'w-full p-3 border rounded-lg bg-gray-50', 'rows': 2, 'placeholder': 'Opcional...'}),
        }