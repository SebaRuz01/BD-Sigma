import os
import requests
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.views import TokenObtainPairView

from .permissions import TieneModuloActivo, EsSuperAdmin, EsAdminTaller
from .models import (
    Taller, Usuario, Modulo, ModuloContratado,
    Tecnico, Repuesto, OrdenTrabajo, OrdenRepuesto,
    Comuna, Cliente, Vehiculo
)
from .serializers import (
    TallerSerializer, UsuarioSerializer,
    ModuloSerializer, ModuloContratadoSerializer,
    TecnicoSerializer, RepuestoSerializer,
    OrdenTrabajoSerializer, OrdenTrabajoCreateSerializer, OrdenRepuestoSerializer,
    CustomTokenObtainPairSerializer,
    TecnicoCreateSerializer,
    TallerCreateSerializer,
    ComunaSerializer, ClienteSerializer, VehiculoSerializer,
)


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


class ComunaViewSet(viewsets.ModelViewSet):
    queryset = Comuna.objects.all()
    serializer_class = ComunaSerializer
    permission_classes = [IsAuthenticated]


class ClienteViewSet(viewsets.ModelViewSet):
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        usuario = self.request.user
        if usuario.taller_id is None:
            return Cliente.objects.all()
        return Cliente.objects.filter(taller_id=usuario.taller_id)

    def perform_create(self, serializer):
        serializer.save(taller_id=self.request.user.taller_id)


class VehiculoViewSet(viewsets.ModelViewSet):
    serializer_class = VehiculoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        usuario = self.request.user
        if usuario.taller_id is None:
            return Vehiculo.objects.all()
        return Vehiculo.objects.filter(cliente__taller_id=usuario.taller_id)


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
    permission_classes = [IsAuthenticated, TieneModuloActivo, EsAdminTaller]
    modulo_requerido = 'ordenes'

    def get_queryset(self):
        usuario = self.request.user
        if usuario.taller_id is None:
            return OrdenTrabajo.objects.all()
        return OrdenTrabajo.objects.filter(taller_id=usuario.taller_id)

    def get_serializer_class(self):
        if self.action == 'create':
            return OrdenTrabajoCreateSerializer
        return OrdenTrabajoSerializer

    def perform_create(self, serializer):
        orden = serializer.save()
        
        # Enviar correo de creación mediante Brevo
        cliente_email = orden.vehiculo.cliente.email if (orden.vehiculo and orden.vehiculo.cliente) else None
        if cliente_email:
            try:
                url = "https://api.brevo.com/v3/smtp/email"
                headers = {
                    "accept": "application/json",
                    "api-key": os.environ.get("BREVO_API_KEY"),
                    "content-type": "application/json"
                }
                nombre_taller = orden.taller.nombre_comercial if orden.taller else "nuestro taller"
                cliente_nombre = orden.vehiculo.cliente.nombre
                vehiculo_info = f"{orden.vehiculo.modelo} (Patente: {orden.vehiculo.patente})"
                
                # Obtener teléfono del técnico si está asignado
                tecnico_telefono = orden.tecnico.usuario.telefono if (orden.tecnico and orden.tecnico.usuario and orden.tecnico.usuario.telefono) else 'No asignado'
                
                payload = {
                    "sender": {"name": "SIGMA Taller", "email": "sebaruz2004@gmail.com"},
                    "to": [{"email": cliente_email}],
                    "subject": f"Orden creada en {nombre_taller} - Código: {orden.codigo_seguimiento}",
                    "htmlContent": f"""
                        <p>Hola <strong>{cliente_nombre}</strong>,</p>
                        <p>Hemos registrado tu vehículo (<strong>{vehiculo_info}</strong>) en <strong>{nombre_taller}</strong>.</p>
                        <p>Teléfono de contacto del técnico asignado: <strong>{tecnico_telefono}</strong></p>
                        <p>Puedes hacer seguimiento del estado de tu orden en tiempo real utilizando tu código único: <strong>{orden.codigo_seguimiento}</strong></p>
                    """
                }
                response = requests.post(url, json=payload, headers=headers)
                if response.status_code in [200, 201, 202]:
                    print(f"Correo de creación enviado exitosamente vía Brevo a {cliente_email}")
                else:
                    print(f"Error Brevo al crear orden: {response.text}")
            except Exception as e:
                print(f"Excepción al conectar con Brevo (creación): {e}")

    def perform_update(self, serializer):
        orden_antigua = self.get_object()
        estado_anterior = orden_antigua.estado

        orden_actualizada = serializer.save()
        
        if estado_anterior != orden_actualizada.estado:
            cliente_email = orden_actualizada.vehiculo.cliente.email if (orden_actualizada.vehiculo and orden_actualizada.vehiculo.cliente) else None
            if cliente_email:
                try:
                    url = "https://api.brevo.com/v3/smtp/email"
                    headers = {
                        "accept": "application/json",
                        "api-key": os.environ.get("BREVO_API_KEY"),
                        "content-type": "application/json"
                    }
                    nombre_taller = orden_actualizada.taller.nombre_comercial if orden_actualizada.taller else "nuestro taller"
                    cliente_nombre = orden_actualizada.vehiculo.cliente.nombre
                    tecnico_telefono = orden_actualizada.tecnico.usuario.telefono if (orden_actualizada.tecnico and orden_actualizada.tecnico.usuario and orden_actualizada.tecnico.usuario.telefono) else 'No asignado'

                    payload = {
                        "sender": {"name": "SIGMA Taller", "email": "sebaruz2004@gmail.com"},
                        "to": [{"email": cliente_email}],
                        "subject": f"Actualización en {nombre_taller} - Orden {orden_actualizada.codigo_seguimiento}",
                        "htmlContent": f"""
                            <p>Hola <strong>{cliente_nombre}</strong>,</p>
                            <p>El estado de tu vehículo en <strong>{nombre_taller}</strong> ha cambiado a: <strong>{orden_actualizada.estado}</strong>.</p>
                            <p>Teléfono de contacto del técnico asignado: <strong>{tecnico_telefono}</strong></p>
                            <p>Puedes revisar el progreso en tiempo real usando tu código de seguimiento único: <strong>{orden_actualizada.codigo_seguimiento}</strong></p>
                        """
                    }
                    response = requests.post(url, json=payload, headers=headers)
                    if response.status_code in [200, 201, 202]:
                        print(f"Correo de actualización enviado exitosamente vía Brevo a {cliente_email}")
                    else:
                        print(f"Error de Brevo al enviar correo de actualización: {response.text}")
                except Exception as e:
                    print(f"Excepción al conectar con Brevo en actualización: {e}")


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
        instance.repuesto.stock_actual += instance.cantidad
        instance.repuesto.save()
        instance.delete()


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
            'equipo': f"{orden.vehiculo.modelo} — {orden.vehiculo.patente}".strip(' —'),
            'estado': orden.estado,
            'cliente_nombre': orden.vehiculo.cliente.nombre,
            'tecnico_nombre': tecnico_nombre,
        })