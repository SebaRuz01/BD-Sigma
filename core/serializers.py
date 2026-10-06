from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed
from .models import (
    Taller, Usuario, Modulo, ModuloContratado,
    Tecnico, Repuesto, OrdenTrabajo, OrdenRepuesto,
    Comuna, Cliente, Vehiculo, Cita
)


class ComunaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comuna
        fields = '__all__'


class TallerSerializer(serializers.ModelSerializer):
    comuna_nombre = serializers.SerializerMethodField()
    comuna_region = serializers.SerializerMethodField()

    class Meta:
        model = Taller
        fields = '__all__'

    def get_comuna_nombre(self, obj):
        return obj.comuna.nombre if obj.comuna else ''

    def get_comuna_region(self, obj):
        return obj.comuna.region if obj.comuna else ''

    def update(self, instance, validated_data):
        # Capturamos los datos extra que envía tu frontend de React
        request = self.context.get('request')
        if request and hasattr(request, 'data'):
            c_nombre = request.data.get('comuna_nombre')
            c_region = request.data.get('comuna_region')
            
            # Si enviaron un nombre de comuna, creamos/buscamos la comuna en la BD
            if c_nombre is not None:
                if c_nombre.strip() == '':
                    instance.comuna = None
                else:
                    comuna, _ = Comuna.objects.get_or_create(
                        nombre=c_nombre, 
                        defaults={'region': c_region or 'Sin especificar'}
                    )
                    instance.comuna = comuna # Asignamos el comuna_id automáticamente

        # Guardamos el resto de los campos estandar (calle, numero, rubro, etc)
        return super().update(instance, validated_data)


class TallerCreateSerializer(serializers.ModelSerializer):
    admin_username = serializers.CharField(write_only=True)
    admin_password = serializers.CharField(write_only=True)
    admin_nombre = serializers.CharField(write_only=True)
    admin_apellido = serializers.CharField(write_only=True, required=False, allow_blank=True)
    comuna_nombre = serializers.CharField(write_only=True, required=False, allow_blank=True)
    comuna_region = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Taller
        fields = [
            'id', 'nombre_comercial', 'rut', 'rubro', 'calle', 'numero', 'estado',
            'comuna_nombre', 'comuna_region',
            'admin_username', 'admin_password', 'admin_nombre', 'admin_apellido',
        ]

    def create(self, validated_data):
        admin_username = validated_data.pop('admin_username')
        admin_password = validated_data.pop('admin_password')
        admin_nombre = validated_data.pop('admin_nombre')
        admin_apellido = validated_data.pop('admin_apellido', '')
        comuna_nombre = validated_data.pop('comuna_nombre', '')
        comuna_region = validated_data.pop('comuna_region', '')

        comuna = None
        if comuna_nombre:
            comuna, _ = Comuna.objects.get_or_create(
                nombre=comuna_nombre, region=comuna_region or 'Sin especificar'
            )

        taller = Taller.objects.create(comuna=comuna, **validated_data)

        Usuario.objects.create_user(
            username=admin_username,
            password=admin_password,
            rol='admin_taller',
            taller=taller,
            first_name=admin_nombre,
            last_name=admin_apellido,
        )
        return taller


class ModuloSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modulo
        fields = '__all__'


class ModuloContratadoSerializer(serializers.ModelSerializer):
    modulo_nombre = serializers.CharField(source='modulo.nombre', read_only=True)
    modulo_slug = serializers.CharField(source='modulo.slug', read_only=True)

    class Meta:
        model = ModuloContratado
        fields = '__all__'


class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    telefono = serializers.CharField(required=False, allow_blank=True)

    class Meta:
