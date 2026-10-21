from rest_framework.permissions import BasePermission
from .models import ModuloContratado


class EsSuperAdmin(BasePermission):
    message = "Solo un super-admin puede realizar esta acción."

    def has_permission(self, request, view):
        usuario = request.user
        return usuario.is_authenticated and usuario.rol == 'super_admin'


class EsAdminTaller(BasePermission):
    message = "Solo el administrador del taller puede realizar esta acción."

    def has_permission(self, request, view):
        usuario = request.user
        # Validación estricta: Solo pasa si está autenticado y su rol es EXACTAMENTE 'admin_taller'
        return bool(
            usuario and 
            usuario.is_authenticated and 
            usuario.rol == 'admin_taller'
        )


class TieneModuloActivo(BasePermission):
    message = "Tu taller no tiene contratado este módulo."

    def has_permission(self, request, view):
        modulo_slug = getattr(view, 'modulo_requerido', None)
        if modulo_slug is None:
            return True

        usuario = request.user
        if not usuario.is_authenticated:
            return False

        # El cliente no tiene taller asignado
        if getattr(usuario, 'rol', None) == 'cliente':
            return True

        if usuario.taller_id is None and usuario.rol == 'super_admin':
            return True

        if usuario.taller_id is None:
            return False

        if usuario.taller.estado == 'suspendido':
            self.message = "Tu taller está suspendido. Contacta a soporte para reactivarlo."
            return False

        return ModuloContratado.objects.filter(
            taller_id=usuario.taller_id,
            modulo__slug=modulo_slug,
            activo=True
        ).exists()
