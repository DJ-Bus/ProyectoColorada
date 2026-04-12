from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required # <-- ¡Súper importante!
from .forms import VentaSucursalForm
from .models import VentaSucursal, Producto, Empleado

@login_required(login_url='/admin/login/')
def dashboard_ventas(request):
    if request.method == 'POST':
        form = VentaSucursalForm(request.POST)
        if form.is_valid():
            form.save() # ¡Aquí ocurre la magia! Se guarda en Supabase
            return redirect('panaderia:dashboard_ventas')
    else:
        form = VentaSucursalForm()

    # Traemos las últimas 5 ventas para que el empleado vea que sí se guardó
    ultimas_ventas = VentaSucursal.objects.all().order_by('-id')[:5]
    
    return render(request, 'ventas.html', {
        'form': form,
        'ultimas_ventas': ultimas_ventas
    })