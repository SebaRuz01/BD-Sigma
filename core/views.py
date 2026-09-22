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
                
                # Extracción mejorada de los datos del técnico
                if orden.tecnico and orden.tecnico.usuario:
                    t_nombre = f"{orden.tecnico.usuario.first_name} {orden.tecnico.usuario.last_name}".strip() or orden.tecnico.usuario.username
                    t_email = orden.tecnico.usuario.email or "No registrado"
                    t_telefono = orden.tecnico.usuario.telefono or "No registrado"
                    tecnico_html = f"""
                        <p style="margin: 0 0 5px 0; font-size: 16px; color: #334155;"><strong>Técnico asignado:</strong> {t_nombre}</p>
                        <p style="margin: 0 0 5px 0; font-size: 14px; color: #475569;">✉️ {t_email}</p>
                        <p style="margin: 0; font-size: 14px; color: #475569;">📱 {t_telefono}</p>
                    """
                else:
                    tecnico_html = '<p style="margin: 0; font-size: 16px; color: #334155;"><strong>Técnico asignado:</strong> No asignado</p>'
                
                payload = {
                    "sender": {"name": "SIGMA Taller", "email": "sebaruz2004@gmail.com"},
                    "to": [{"email": cliente_email}],
                    "subject": f"Ingreso registrado en {nombre_taller} - Código: {orden.codigo_seguimiento}",
                    "htmlContent": f"""
                    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7fb; padding: 40px 20px; margin: 0;">
                        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.05);">
                            
                            <div style="background-color: #0f172a; padding: 30px 20px; text-align: center;">
                                <img src="https://i.ibb.co/8Zd31j3/logo-CAymw-Kvn.png" alt="SIGMA" style="height: 60px; width: auto; margin-bottom: 15px; display: block; margin-left: auto; margin-right: auto;" />
                                <p style="color: #94a3b8; margin: 0; font-size: 14px; letter-spacing: 1px;">Gestión de Taller Automotriz</p>
                            </div>
                            
                            <div style="padding: 40px 30px;">
                                <h2 style="margin-top: 0; color: #1e293b; font-size: 22px;">Hola {cliente_nombre},</h2>
                                <p style="font-size: 16px; line-height: 1.6; color: #475569; margin-bottom: 25px;">
                                    Hemos registrado exitosamente tu vehículo en <strong>{nombre_taller}</strong>.
                                </p>
                                
                                <div style="margin: 30px 0; padding: 20px; background-color: #f8fafc; border-radius: 12px; border: 1px solid #e2e8f0;">
                                    <p style="margin: 0 0 10px 0; font-size: 14px; color: #64748b; text-transform: uppercase; font-weight: bold; letter-spacing: 1px;">Detalles del Ingreso</p>
                                    <p style="margin: 0 0 15px 0; font-size: 16px; color: #334155; padding-bottom: 10px; border-bottom: 1px solid #e2e8f0;"><strong>Vehículo:</strong> {vehiculo_info}</p>
                                    {tecnico_html}
                                </div>
                                
                                <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 35px 0;" />
                                
                                <div style="text-align: center;">
                                    <p style="font-size: 14px; color: #64748b; margin-bottom: 10px;">Tu código único para seguimiento en línea:</p>
                                    <div style="display: inline-block; background-color: #1e293b; color: #ffffff; font-size: 24px; font-weight: bold; letter-spacing: 4px; padding: 12px 25px; border-radius: 8px;">
                                        {orden.codigo_seguimiento}
                                    </div>
                                </div>
                            </div>
                            
                            <div style="background-color: #f8fafc; padding: 20px; text-align: center; border-top: 1px solid #f1f5f9;">
                                <p style="margin: 0; font-size: 12px; color: #94a3b8;">
                                    Este es un correo automático generado por el sistema SIGMA.<br>Por favor no respondas a este mensaje.
                                </p>
                            </div>
                            
                        </div>
                    </div>
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
                    
                    # Extracción de datos del técnico para correo de actualización
                    if orden_actualizada.tecnico and orden_actualizada.tecnico.usuario:
                        t_nombre = f"{orden_actualizada.tecnico.usuario.first_name} {orden_actualizada.tecnico.usuario.last_name}".strip() or orden_actualizada.tecnico.usuario.username
                        t_email = orden_actualizada.tecnico.usuario.email or "No registrado"
                        t_telefono = orden_actualizada.tecnico.usuario.telefono or "No registrado"
                        tecnico_html = f"""
                            <p style="margin: 0 0 5px 0; font-size: 15px; color: #334155;"><strong>Técnico asignado:</strong> {t_nombre}</p>
                            <p style="margin: 0 0 5px 0; font-size: 14px; color: #475569;">✉️ {t_email}</p>
                            <p style="margin: 0; font-size: 14px; color: #475569;">📱 {t_telefono}</p>
                        """
                    else:
                        tecnico_html = '<p style="margin: 0; font-size: 15px; color: #334155;"><strong>Técnico asignado:</strong> No asignado</p>'

                    payload = {
                        "sender": {"name": "SIGMA Taller", "email": "sebaruz2004@gmail.com"},
                        "to": [{"email": cliente_email}],
                        "subject": f"Actualización en {nombre_taller} - Orden {orden_actualizada.codigo_seguimiento}",
                        "htmlContent": f"""
                        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7fb; padding: 40px 20px; margin: 0;">
                            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.05);">
                                
                                <div style="background-color: #0f172a; padding: 30px 20px; text-align: center;">
                                    <img src="https://i.ibb.co/8Zd31j3/logo-CAymw-Kvn.png" alt="SIGMA" style="height: 60px; width: auto; margin-bottom: 15px; display: block; margin-left: auto; margin-right: auto;" />
                                    <p style="color: #94a3b8; margin: 0; font-size: 14px; letter-spacing: 1px;">Gestión de Taller Automotriz</p>
                                </div>
                                
                                <div style="padding: 40px 30px;">
                                    <h2 style="margin-top: 0; color: #1e293b; font-size: 22px;">Hola {cliente_nombre},</h2>
                                    <p style="font-size: 16px; line-height: 1.6; color: #475569; margin-bottom: 25px;">
                                        El estado de tu vehículo en <strong>{nombre_taller}</strong> ha sido actualizado.
                                    </p>
                                    
                                    <div style="text-align: center; margin: 30px 0; padding: 20px; background-color: #eff6ff; border-radius: 12px; border: 1px solid #bfdbfe;">
                                        <p style="margin: 0; font-size: 14px; color: #64748b; text-transform: uppercase; font-weight: bold; letter-spacing: 1px;">Nuevo Estado</p>
                                        <p style="margin: 10px 0 0 0; font-size: 24px; color: #2563eb; font-weight: 900; text-transform: capitalize;">
                                            {orden_actualizada.estado}
                                        </p>
                                    </div>
                                    
                                    <div style="background-color: #f8fafc; padding: 15px 20px; border-radius: 8px; border-left: 4px solid #3b82f6;">
                                        {tecnico_html}
                                    </div>
                                    
                                    <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 35px 0;" />
                                    
                                    <div style="text-align: center;">
                                        <p style="font-size: 14px; color: #64748b; margin-bottom: 10px;">Tu código único de seguimiento en tiempo real:</p>
                                        <div style="display: inline-block; background-color: #1e293b; color: #ffffff; font-size: 24px; font-weight: bold; letter-spacing: 4px; padding: 12px 25px; border-radius: 8px;">
                                            {orden_actualizada.codigo_seguimiento}
                                        </div>
                                    </div>
                                </div>
                                
                                <div style="background-color: #f8fafc; padding: 20px; text-align: center; border-top: 1px solid #f1f5f9;">
                                    <p style="margin: 0; font-size: 12px; color: #94a3b8;">
                                        Este es un correo automático generado por el sistema SIGMA.<br>Por favor no respondas a este mensaje.
                                    </p>
                                </div>
                                
                            </div>
                        </div>
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
