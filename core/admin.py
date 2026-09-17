from django.contrib import admin
from .models import (
    Taller, Usuario, Modulo, ModuloContratado,
    Tecnico, Repuesto, OrdenTrabajo, OrdenRepuesto,
    Comuna, Vehiculo
)


admin.site.register(Comuna)
admin.site.register(Vehiculo)

admin.site.register(Taller)
admin.site.register(Usuario)
admin.site.register(Modulo)
admin.site.register(ModuloContratado)
admin.site.register(Tecnico)
admin.site.register(Repuesto)

@admin.register(OrdenTrabajo)
class OrdenTrabajoAdmin(admin.ModelAdmin):
    # Actualizado con 'vehiculo' en lugar de 'equipo' y 'cliente'
    list_display = ('id', 'codigo_seguimiento', 'vehiculo', 'estado', 'fecha_recepcion')
    search_fields = ('codigo_seguimiento', 'vehiculo__patente', 'vehiculo__modelo')

admin.site.register(OrdenRepuesto)
