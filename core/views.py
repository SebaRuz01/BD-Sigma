import os
import requests
from rest_framework import viewsets, permissions
from rest_framework.permissions import IsAuthenticated, AllowAny
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
    queryset = OrdenRepuesto.objects.all()
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
        orden = serializer.save(taller_id=self.request.user.taller_id)
        
        # Enviar correo al crear la orden si tiene email registrado
        if orden.cliente_email:
            try:
                url = "https://api.brevo.com/v3/smtp/email"
                headers = {
                    "accept": "application/json",
                    "api-key": os.environ.get("BREVO_API_KEY"),
                    "content-type": "application/json"
                }
                payload = {
                    "sender": {"name": "SIGMA Taller", "email": "sebaruz2004@gmail.com"},
                    "to": [{"email": orden.cliente_email}],
                    "subject": f"Orden de trabajo creada - Código: {orden.codigo_seguimiento}",
                    "htmlContent": f"""
                        <p>Hola <strong>{orden.cliente_nombre}</strong>,</p>
                        <p>Hemos registrado tu equipo/vehículo (<strong>{orden.equipo}</strong>) en nuestro taller.</p>
                        <p>Puedes hacer seguimiento del estado de tu orden en tiempo real utilizando tu código único: <strong>{orden.codigo_seguimiento}</strong></p>
                    """
                }
                response = requests.post(url, json=payload, headers=headers)
                if response.status_code == 201:
                    print(f"Correo de creación enviado a {orden.cliente_email}")
                else:
                    print(f"Error Brevo al crear orden: {response.text}")
            except Exception as e:
                print(f"Excepción al conectar con Brevo (creación): {e}")

    def perform_update(self, serializer):
        instancia_antigua = self.get_object()
        estado_anterior = instancia_antigua.estado

        orden_actualizada = serializer.save()
        
        # Si el estado cambió y el cliente tiene correo registrado
        if estado_anterior != orden_actualizada.estado:
            if orden_actualizada.cliente_email:
                try:
                    url = "https://api.brevo.com/v3/smtp/email"
                    headers = {
                        "accept": "application/json",
                        "api-key": os.environ.get("BREVO_API_KEY"),
                        "content-type": "application/json"
                    }
                    payload = {
                        "sender": {"name": "SIGMA Taller", "email": "sebaruz2004@gmail.com"},
                        "to": [{"email": orden_actualizada.cliente_email}],
                        "subject": f"Actualización de tu vehículo - Orden {orden_actualizada.codigo_seguimiento}",
                        "htmlContent": f"""
                            <p>Hola <strong>{orden_actualizada.cliente_nombre}</strong>,</p>
                            <p>El estado de tu vehículo ha cambiado a: <strong>{orden_actualizada.estado}</strong>.</p>
                            <p>Puedes revisar el progreso en tiempo real usando tu código de seguimiento único: <strong>{orden_actualizada.codigo_seguimiento}</strong></p>
                        """
                    }
                    response = requests.post(url, json=payload, headers=headers)
                    if response.status_code == 201:
                        print(f"Correo enviado exitosamente vía Brevo a {orden_actualizada.cliente_email}")
                    else:
                        print(f"Error de Brevo al enviar correo: {response.text}")
                except Exception as e:
                    print(f"Excepción al conectar con Brevo: {e}")


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
