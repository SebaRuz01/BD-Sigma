from rest_framework import viewsets, permissions
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from .permissions import TieneModuloActivo, EsSuperAdmin, EsAdminTaller
from rest_framework.exceptions import ValidationError
from .models import (
    Taller, Usuario, Modulo, ModuloContratado,
    Tecnico, Repuesto, OrdenTrabajo, OrdenRepuesto
)
from .serializers import (
    TallerSerializer, UsuarioSerializer,
    ModuloSerializer, ModuloContratadoSerializer,
    TecnicoSerializer, RepuestoSerializer,
    OrdenTrabajoSerializer, OrdenRepuestoSerializer,
    CustomTokenObtainPairSerializer,
    TecnicoCreateSerializer,
    TallerCreateSerializer
)

class OrdenRepuestoViewSet(viewsets.ModelViewSet):
    serializer_class = OrdenRepuestoSerializer
    permission_classes = [IsAuthenticated, TieneModuloActivo]
    modulo_requerido = 'ordenes'

    def get_queryset(self):
        usuario = self.request.user
        if usuario.taller_id is None:
            return OrdenRepuesto.objects.all()
        return OrdenRepuesto.objects.filter(orden__taller_id=usuario.taller_id)

    def perform_create(self, serializer):
        repuesto = serializer.validated_data['repuesto']
        cantidad = serializer.validated_data['cantidad']

        if repuesto.stock_actual < cantidad:
            raise ValidationError(f'Stock insuficiente. Disponible: {repuesto.stock_actual}')

        repuesto.stock_actual -= cantidad
        repuesto.save()
        serializer.save()

    def perform_destroy(self, instance):
        # si se quita un repuesto de una orden, se devuelve el stock
        instance.repuesto.stock_actual += instance.cantidad
        instance.repuesto.save()
        instance.delete()

class TallerViewSet(viewsets.ModelViewSet):
    queryset = Taller.objects.all()
    permission_classes = [IsAuthenticated, EsSuperAdmin]

    def get_serializer_class(self):
        if self.action == 'create':
            return TallerCreateSerializer
        return TallerSerializer


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer


class ModuloViewSet(viewsets.ModelViewSet):
    queryset = Modulo.objects.all()
    serializer_class = ModuloSerializer
    permission_classes = [IsAuthenticated]


class ModuloContratadoViewSet(viewsets.ModelViewSet):
    queryset = ModuloContratado.objects.all()
    serializer_class = ModuloContratadoSerializer
    permission_classes = [IsAuthenticated, EsSuperAdmin]


class TecnicoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, TieneModuloActivo]
    modulo_requerido = 'tecnicos'

    def get_queryset(self):
        usuario = self.request.user
        if usuario.taller_id is None:
            return Tecnico.objects.all()
        return Tecnico.objects.filter(taller_id=usuario.taller_id)

    def get_serializer_class(self):
        if self.action == 'create':
            return TecnicoCreateSerializer
        return TecnicoSerializer


class RepuestoViewSet(viewsets.ModelViewSet):
    serializer_class = RepuestoSerializer
    permission_classes = [IsAuthenticated, TieneModuloActivo]
    modulo_requerido = 'inventario'

    def get_queryset(self):
        usuario = self.request.user
        if usuario.taller_id is None:
            return Repuesto.objects.all()
        return Repuesto.objects.filter(taller_id=usuario.taller_id)

    def perform_create(self, serializer):
        serializer.save(taller_id=self.request.user.taller_id)


class OrdenTrabajoViewSet(viewsets.ModelViewSet):
    serializer_class = OrdenTrabajoSerializer
    permission_classes = [IsAuthenticated, TieneModuloActivo, EsAdminTaller]
    modulo_requerido = 'ordenes'

    def get_queryset(self):
        usuario = self.request.user
        if usuario.taller_id is None:
            return OrdenTrabajo.objects.all()
        return OrdenTrabajo.objects.filter(taller_id=usuario.taller_id)

    def perform_create(self, serializer):
        serializer.save(taller_id=self.request.user.taller_id)

    def perform_update(self, serializer):
        # Capturamos el estado anterior para comparar si realmente cambió (opcional pero recomendado)
        instancia_antigua = self.get_object()
        estado_anterior = instancia_antigua.estado

        # Guardamos la orden actualizada
        orden_actualizada = serializer.save()
        
        # Si el estado cambió y el cliente tiene correo registrado
        if estado_anterior != orden_actualizada.estado:
            if hasattr(orden_actualizada, 'cliente_email') and orden_actualizada.cliente_email:
                try:
                    send_mail(
                        subject=f"Actualización de tu vehículo - Orden {orden_actualizada.codigo_seguimiento}",
                        message=(
                            f"Hola, el estado de tu vehículo ha cambiado a: {orden_actualizada.estado}.\n\n"
                            f"Puedes revisar el progreso en tiempo real usando tu código de seguimiento: {orden_actualizada.codigo_seguimiento}"
                        ),
                        from_email=None,  # Utiliza automáticamente tu DEFAULT_FROM_EMAIL de Gmail configurado en settings.py
                        recipient_list=[orden_actualizada.cliente_email],
                        fail_silently=False,
                    )
                    print(f"Correo enviado exitosamente a {orden_actualizada.cliente_email} con el código {orden_actualizada.codigo_seguimiento}")
                except Exception as e:
                    print(f"Error al enviar correo automático: {e}")


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class OrdenPublicaView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, codigo):
        try:
            orden = OrdenTrabajo.objects.get(codigo_seguimiento=codigo.upper())
        except OrdenTrabajo.DoesNotExist:
            return Response({'detail': 'Orden no encontrada.'}, status=404)

        tecnico_nombre = None
        if orden.tecnico:
            nombre_completo = f"{orden.tecnico.usuario.first_name} {orden.tecnico.usuario.last_name}".strip()
            tecnico_nombre = nombre_completo or orden.tecnico.usuario.username

        return Response({
            'id': orden.id,
            'codigo_seguimiento': orden.codigo_seguimiento,
            'equipo': orden.equipo,
            'estado': orden.estado,
            'cliente_nombre': orden.cliente_nombre,
            'tecnico_nombre': tecnico_nombre,
        })
