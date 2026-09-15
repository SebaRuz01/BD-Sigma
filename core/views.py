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
    Tecnico, Repuesto, OrdenTrabajo, OrdenRepuesto, Cliente, LoginCliente
)
from .serializers import (
    TallerSerializer, UsuarioSerializer,
    ModuloSerializer, ModuloContratadoSerializer,
    TecnicoSerializer, RepuestoSerializer,
    OrdenTrabajoSerializer, OrdenRepuestoSerializer,
    CustomTokenObtainPairSerializer,
    TecnicoCreateSerializer,
    TallerCreateSerializer,
    LoginClienteSerializer
)

class LoginClienteViewSet(viewsets.ModelViewSet):
    queryset = LoginCliente.objects.all()
    serializer_class = LoginClienteSerializer

    def get_permissions(self):
        # Permitir registro libre solo en POST, el resto requiere autenticación
        if self.request.method == 'POST':
            return [AllowAny()]
        return [IsAuthenticated()]

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
        cantidad = int(serializer.validated_data.get('cantidad', 1))

        if repuesto.stock_actual < cantidad:
            raise ValidationError(f'Stock insuficiente. Disponible: {repuesto.stock_actual}')

        serializer.save()
        repuesto.stock_actual -= cantidad
        repuesto.save()

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
    permission_classes = [IsAuthenticated]


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
        taller_id = self.request.user.taller_id
        
        cliente_nombre = self.request.data.get('cliente_nombre')
        cliente_rut = self.request.data.get('cliente_rut', '')
        cliente_email = self.request.data.get('cliente_email')
        cliente_telefono = self.request.data.get('cliente_telefono', '')
        cliente_direccion = self.request.data.get('cliente_direccion', '')
        patente = self.request.data.get('patente', '')

        cliente = None
        if cliente_rut:
            cliente = Cliente.objects.filter(taller_id=taller_id, rut=cliente_rut).first()
        
        if not cliente and cliente_email:
            cliente = Cliente.objects.filter(taller_id=taller_id, email=cliente_email).first()
        
        if not cliente and cliente_telefono:
            cliente = Cliente.objects.filter(taller_id=taller_id, telefono=cliente_telefono).first()

        if not cliente:
            cliente = Cliente.objects.create(
                taller_id=taller_id,
                nombre=cliente_nombre,
                rut=cliente_rut,
                email=cliente_email,
                telefono=cliente_telefono,
                direccion=cliente_direccion
            )
        else:
            if cliente_nombre:
                cliente.nombre = cliente_nombre
            if cliente_rut:
                cliente.rut = cliente_rut
            if cliente_email:
                cliente.email = cliente_email
            if cliente_telefono:
                cliente.telefono = cliente_telefono
            if cliente_direccion:
                cliente.direccion = cliente_direccion
            cliente.save()

        orden = serializer.save(taller_id=taller_id, cliente=cliente, patente=patente)
        
        if orden.cliente and orden.cliente.email:
            try:
                url = "https://api.brevo.com/v3/smtp/email"
                headers = {
                    "accept": "application/json",
                    "api-key": os.environ.get("BREVO_API_KEY"),
                    "content-type": "application/json"
                }
                nombre_taller = orden.taller.nombre_comercial if orden.taller else "nuestro taller"
                payload = {
                    "sender": {"name": "SIGMA Taller", "email": "sebaruz2004@gmail.com"},
                    "to": [{"email": orden.cliente.email}],
                    "subject": f"Orden creada en {nombre_taller} - Código: {orden.codigo_seguimiento}",
                    "htmlContent": f"""
                        <p>Hola <strong>{orden.cliente.nombre}</strong>,</p>
                        <p>Hemos registrado tu vehículo (<strong>{orden.equipo}</strong> - Patente: <strong>{orden.patente or 'N/A'}</strong>) en <strong>{nombre_taller}</strong>.</p>
                        <p>Puedes hacer seguimiento del estado de tu orden en tiempo real utilizando tu código único: <strong>{orden.codigo_seguimiento}</strong></p>
                    """
                }
                requests.post(url, json=payload, headers=headers)
            except Exception as e:
                print(f"Excepción Brevo: {e}")

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
            'patente': orden.patente,
            'estado': orden.estado,
            'cliente_nombre': orden.cliente.nombre if orden.cliente else None,
            'tecnico_nombre': tecnico_nombre,
        })
