from functools import wraps

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden


def staff_required(view_func):
    """
    Decorator que permite acceso solo a usuarios con is_staff=True.
    Debe usarse DESPUÉS de @login_required.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            return HttpResponseForbidden(
                "<h2>Acceso denegado</h2>"
                "<p>Esta sección es solo para el administrador.</p>"
            )
        return view_func(request, *args, **kwargs)
    return wrapper
