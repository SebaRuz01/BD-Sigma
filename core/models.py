from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid


class Taller(models.Model):
    ESTADOS = [
        ('activo', 'Activo'),
        ('suspendido', 'Suspendido'),
        ('prueba', 'Prueba'),
    ]

    nombre_comercial = models.CharField(max_length=150)
    rut = models.CharField(max_length=20, unique=True)
    rubro = models.CharField(max_length=50)
    direccion = models.CharField(max_length=255, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='prueba')
    fecha_alta = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre_comercial


class Usuario(AbstractUser):
    ROLES = [
        ('super_admin', 'Super Admin'),
        ('admin_taller', 'Admin de Taller'),
        ('tecnico', 'Técnico'),
        ('recepcionista', 'Recepcionista'),
    ]

    taller = models.ForeignKey(
        Taller, on_delete=models.CASCADE, null=True, blank=True,
        related_name='usuarios'
    )
    rol = models.CharField(max_length=20, choices=ROLES, default='admin_taller')

    def __str__(self):
        return f"{self.username} ({self.rol})"


class Modulo(models.Model):
    nombre = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre


class ModuloContratado(models.Model):
    taller = models.ForeignKey(Taller, on_delete=models.CASCADE, related_name='modulos_contratados')
    modulo = models.ForeignKey(Modulo, on_delete=models.CASCADE)
    activo = models.BooleanField(default=True)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('taller', 'modulo')

    def __str__(self):
        return f"{self.taller} — {self.modulo} ({'activo' if self.activo else 'inactivo'})"

class Tecnico(models.Model):
    taller = models.ForeignKey(Taller, on_delete=models.CASCADE, related_name='tecnicos')
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='perfil_tecnico')
    especialidad = models.CharField(max_length=100, blank=True)
    eficiencia_promedio = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.usuario.username} — {self.especialidad}"


class Repuesto(models.Model):
    taller = models.ForeignKey(Taller, on_delete=models.CASCADE, related_name='repuestos')
    nombre = models.CharField(max_length=150)
    stock_actual = models.PositiveIntegerField(default=0)
    stock_minimo = models.PositiveIntegerField(default=0)
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.nombre} ({self.taller})"


class OrdenTrabajo(models.Model):
    ESTADOS = [
        ('recibido', 'Recibido'),
        ('diagnostico', 'Diagnóstico'),
        ('en_reparacion', 'En reparación'),
        ('listo', 'Listo para retiro'),
        ('entregado', 'Entregado'),
    ]

    taller = models.ForeignKey(Taller, on_delete=models.CASCADE, related_name='ordenes_trabajo')
    codigo_seguimiento = models.CharField(max_length=12, unique=True, editable=False, blank=True)
    tecnico = models.ForeignKey(Tecnico, on_delete=models.SET_NULL, null=True, blank=True, related_name='ordenes')
    cliente_nombre = models.CharField(max_length=150)
    cliente_telefono = models.CharField(max_length=30, blank=True)
    equipo = models.CharField(max_length=150)
    descripcion_problema = models.TextField(blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='recibido')
    fecha_recepcion = models.DateTimeField(auto_now_add=True)
    fecha_estimada = models.DateTimeField(null=True, blank=True)
    fecha_entrega = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"OT-{self.id} — {self.equipo} ({self.estado})"

    def save(self, *args, **kwargs):
        if not self.codigo_seguimiento:
            self.codigo_seguimiento = uuid.uuid4().hex[:8].upper()
        super().save(*args, **kwargs)
    


class OrdenRepuesto(models.Model):
    orden = models.ForeignKey(OrdenTrabajo, on_delete=models.CASCADE, related_name='repuestos_usados')
    repuesto = models.ForeignKey(Repuesto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('orden', 'repuesto')

    def __str__(self):
        return f"{self.orden} — {self.repuesto} x{self.cantidad}"