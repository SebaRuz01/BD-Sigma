from rest_framework import serializers
from .models import (
    Taller, Usuario, Modulo, ModuloContratado,
    Tecnico, Repuesto, OrdenTrabajo, OrdenRepuesto
)
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class TallerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Taller
        fields = '__all__'


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
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'rol', 'taller']   

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['taller_id'] = user.taller_id
        token['rol'] = user.rol
        token['username'] = user.username
        return token

class TecnicoSerializer(serializers.ModelSerializer):
    nombre = serializers.SerializerMethodField()

    class Meta:
        model = Tecnico
        fields = '__all__'

    def get_nombre(self, obj):
        nombre_completo = f"{obj.usuario.first_name} {obj.usuario.last_name}".strip()
        return nombre_completo or obj.usuario.username

class TecnicoCreateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    nombre = serializers.CharField(write_only=True)
    apellido = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Tecnico
        fields = ['id', 'username', 'password', 'nombre', 'apellido', 'especialidad', 'eficiencia_promedio']

    def create(self, validated_data):
        username = validated_data.pop('username')
        password = validated_data.pop('password')
        nombre = validated_data.pop('nombre')
        apellido = validated_data.pop('apellido', '')
        taller = self.context['request'].user.taller
        usuario = Usuario.objects.create_user(
            username=username, password=password, rol='tecnico', taller=taller,
            first_name=nombre, last_name=apellido
        )
        return Tecnico.objects.create(usuario=usuario, taller=taller, **validated_data)

class RepuestoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Repuesto
        fields = '__all__'
        read_only_fields = ['taller']

class OrdenRepuestoSerializer(serializers.ModelSerializer):
    repuesto_nombre = serializers.CharField(source='repuesto.nombre', read_only=True)
    # Agregamos este campo para incluir la compatibilidad y el stock
    repuesto_detalles = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = OrdenRepuesto
        fields = ['id', 'orden', 'repuesto', 'repuesto_nombre', 'repuesto_detalles', 'cantidad']

    def get_repuesto_detalles(self, obj):
        compat = obj.repuesto.compatibilidades or 'Universal'
        return f"{obj.repuesto.nombre} ({compat}) - Stock: {obj.repuesto.stock_actual}"


class OrdenTrabajoSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source='cliente.nombre', read_only=True)
    cliente_email = serializers.EmailField(source='cliente.email', read_only=True)
    cliente_telefono = serializers.CharField(source='cliente.telefono', read_only=True)
    tecnico_nombre = serializers.CharField(source='tecnico.usuario.username', read_only=True)

    class Meta:
        model = OrdenTrabajo
        fields = [
            'id', 'taller', 'codigo_seguimiento', 'tecnico', 'tecnico_nombre',
            'cliente', 'cliente_nombre', 'cliente_email', 'cliente_telefono',
            'equipo', 'descripcion_problema', 'estado', 'fecha_recepcion', 'repuestos_usados'
        ]
        read_only_fields = ['taller', 'codigo_seguimiento', 'cliente']

class TallerCreateSerializer(serializers.ModelSerializer):
    admin_username = serializers.CharField(write_only=True)
    admin_password = serializers.CharField(write_only=True)
    admin_nombre = serializers.CharField(write_only=True)
    admin_apellido = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Taller
        fields = [
            'id', 'nombre_comercial', 'rut', 'rubro', 'direccion', 'estado',
            'admin_username', 'admin_password', 'admin_nombre', 'admin_apellido',
        ]

    def create(self, validated_data):
        admin_username = validated_data.pop('admin_username')
        admin_password = validated_data.pop('admin_password')
        admin_nombre = validated_data.pop('admin_nombre')
        admin_apellido = validated_data.pop('admin_apellido', '')

        taller = Taller.objects.create(**validated_data)

        Usuario.objects.create_user(
            username=admin_username,
            password=admin_password,
            rol='admin_taller',
            taller=taller,
            first_name=admin_nombre,
            last_name=admin_apellido,
        )
        return taller
