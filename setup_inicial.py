"""
Script de datos iniciales para Panadería La Colorada.
Uso: python3 manage.py shell < setup_inicial.py
"""
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.contrib.auth.models import User
from panaderia.models import Empleado, Insumo, Producto

# ── Productos (panes) ────────────────────────────────────────────────────────
PRODUCTOS = [
    {"nombre": "Concha",     "precio_publico": 12.00, "precio_mayoreo": 8.00},
    {"nombre": "Coronada",   "precio_publico": 15.00, "precio_mayoreo": 10.00},
    {"nombre": "Granada",    "precio_publico": 12.00, "precio_mayoreo": 8.00},
    {"nombre": "Chino",      "precio_publico": 10.00, "precio_mayoreo": 7.00},
    {"nombre": "Nido",       "precio_publico": 12.00, "precio_mayoreo": 8.00},
    {"nombre": "Pan Mini",   "precio_publico": 5.00,  "precio_mayoreo": 3.50},
    {"nombre": "Dona",       "precio_publico": 15.00, "precio_mayoreo": 10.00},
    {"nombre": "Cuerno",     "precio_publico": 12.00, "precio_mayoreo": 8.00},
    {"nombre": "Polvorón",   "precio_publico": 10.00, "precio_mayoreo": 7.00},
    {"nombre": "Mantecada",  "precio_publico": 12.00, "precio_mayoreo": 8.00},
]

for p in PRODUCTOS:
    obj, created = Producto.objects.get_or_create(
        nombre=p["nombre"],
        defaults={
            "precio_publico": p["precio_publico"],
            "precio_mayoreo": p["precio_mayoreo"],
        },
    )
    status = "✅ Creado" if created else "⏭️  Ya existe"
    print(f"  {status}: {obj}")

# ── Insumos ───────────────────────────────────────────────────────────────────
INSUMOS = [
    {"nombre": "Harina",    "unidad": "bulto"},
    {"nombre": "Huevo",     "unidad": "pieza"},
    {"nombre": "Azúcar",    "unidad": "kg"},
    {"nombre": "Manteca",   "unidad": "kg"},
    {"nombre": "Margarina", "unidad": "kg"},
    {"nombre": "Cocoa",     "unidad": "kg"},
    {"nombre": "Levadura",  "unidad": "pieza"},
    {"nombre": "Royal",     "unidad": "pieza"},
    {"nombre": "Leche",     "unidad": "litro"},
    {"nombre": "Sal",       "unidad": "kg"},
]

for i in INSUMOS:
    obj, created = Insumo.objects.get_or_create(
        nombre=i["nombre"],
        defaults={"unidad": i["unidad"]},
    )
    status = "✅ Creado" if created else "⏭️  Ya existe"
    print(f"  {status}: {obj}")

# ── Usuarios y empleados ─────────────────────────────────────────────────────
# Dueño (superuser) — si no existe
if not User.objects.filter(username="admin").exists():
    admin_user = User.objects.create_superuser(
        username="admin",
        password="colorada2024",
        first_name="Dueño",
        last_name="La Colorada",
    )
    Empleado.objects.get_or_create(
        usuario=admin_user,
        defaults={"nombre": "Dueño", "rol": "sucursal"},
    )
    print("  ✅ Superusuario 'admin' creado (contraseña: colorada2024)")
else:
    print("  ⏭️  Superusuario 'admin' ya existe")

# Empleados de ejemplo
EMPLEADOS = [
    {"username": "maria",  "nombre": "María García",   "rol": "sucursal", "password": "venta2024"},
    {"username": "juan",   "nombre": "Juan López",     "rol": "puesto",   "password": "venta2024"},
    {"username": "carlos", "nombre": "Carlos Mendoza", "rol": "puesto",   "password": "venta2024"},
]

for e in EMPLEADOS:
    user, user_created = User.objects.get_or_create(
        username=e["username"],
        defaults={
            "first_name": e["nombre"].split()[0],
            "last_name": " ".join(e["nombre"].split()[1:]),
        },
    )
    if user_created:
        user.set_password(e["password"])
        user.save()

    emp, emp_created = Empleado.objects.get_or_create(
        usuario=user,
        defaults={"nombre": e["nombre"], "rol": e["rol"]},
    )
    status = "✅ Creado" if emp_created else "⏭️  Ya existe"
    print(f"  {status}: {emp} (user: {e['username']})")

print("\n🍞 ¡Datos iniciales cargados correctamente!")
print("   Admin: admin / colorada2024")
print("   Empleados: maria, juan, carlos / venta2024")
