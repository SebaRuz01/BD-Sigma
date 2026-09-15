from django.contrib import admin
from .models import (
    Taller, Usuario, Modulo, ModuloContratado,
    Tecnico, Repuesto, OrdenTrabajo, OrdenRepuesto
)

admin.site.register(Taller)
admin.site.register(Usuario)
admin.site.register(Modulo)
admin.site.register(ModuloContratado)
admin.site.register(Tecnico)
admin.site.register(Repuesto)

@admin.register(OrdenTrabajo)
class OrdenTrabajoAdmin(admin.ModelAdmin):
    # Cambiamos 'cliente_nombre' por 'cliente' que es el campo real del modelo original
    list_display = ['id', 'codigo_seguimiento', 'equipo', 'cliente', 'estado']

admin.site.register(OrdenRepuesto)
