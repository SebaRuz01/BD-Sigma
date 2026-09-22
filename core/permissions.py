from rest_framework.permissions import BasePermission

from .models import ModuloContratado


class TieneModuloActivo(BasePermission):
    """
    Permite el acceso solo si el taller del usuario autenticado
    tiene contratado y activo el módulo indicado en `modulo_requerido`
    del ViewSet que use este permiso.
    """

    message = "Tu taller no tiene contratado este módulo."

    def has_permission(self, request, view):
        modulo_slug = getattr(view, 'modulo_requerido', None)

        if modulo_slug is None:
            # Si el ViewSet no declara módulo, no se restringe por esta vía.
            return True

        usuario = request.user

        if not usuario.is_authenticated:
            return False

        # El super-admin (sin taller asignado) siempre pasa.
        if usuario.taller_id is None and usuario.rol == 'super_admin':
            return True

        if usuario.taller_id is None:
            return False

        return ModuloContratado.objects.filter(
            taller_id=usuario.taller_id,
            modulo__slug=modulo_slug,
            activo=True
        ).exists()


class EsSuperAdmin(BasePermission):
    message = "Solo un super-admin puede realizar esta acción."

    def has_permission(self, request, view):
        usuario = request.user
        return usuario.is_authenticated and usuario.rol == 'super_admin'

class TieneModuloActivo(BasePermission):
    message = "Tu taller no tiene contratado este módulo."

    def has_permission(self, request, view):
        modulo_slug = getattr(view, 'modulo_requerido', None)
        if modulo_slug is None:
            return True

        usuario = request.user
        if not usuario.is_authenticated:
            return False

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

class EsAdminTaller(BasePermission):
    message = "Solo el administrador del taller puede realizar esta acción."

    def has_permission(self, request, view):
        # Para lectura y creación, cualquier usuario autenticado del taller pasa.
        if request.method not in ('DELETE',):
            return True
        usuario = request.user
        return usuario.is_authenticated and usuario.rol in ('admin_taller', 'super_admin')