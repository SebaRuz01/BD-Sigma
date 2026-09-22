from django.contrib import admin
from .models import (
    Taller, Usuario, Modulo, ModuloContratado,
<<<<<<< HEAD
    Tecnico, Repuesto, OrdenTrabajo, OrdenRepuesto,
    Comuna, Cliente, Vehiculo
=======
    Tecnico, Repuesto, OrdenTrabajo, OrdenRepuesto
>>>>>>> 7e6817b1da587f52b1f6b667dee2846aa38e5665
)

admin.site.register(Taller)
admin.site.register(Usuario)
admin.site.register(Modulo)
admin.site.register(ModuloContratado)
admin.site.register(Tecnico)
admin.site.register(Repuesto)
<<<<<<< HEAD
admin.site.register(Comuna)
admin.site.register(Cliente)
admin.site.register(Vehiculo)


@admin.register(OrdenTrabajo)
class OrdenTrabajoAdmin(admin.ModelAdmin):
    list_display = ['id', 'codigo_seguimiento', 'vehiculo', 'estado']


=======
@admin.register(OrdenTrabajo)
class OrdenTrabajoAdmin(admin.ModelAdmin):
    list_display = ('id', 'codigo_seguimiento', 'equipo', 'cliente', 'estado', 'fecha_recepcion')
>>>>>>> 7e6817b1da587f52b1f6b667dee2846aa38e5665
admin.site.register(OrdenRepuesto)
