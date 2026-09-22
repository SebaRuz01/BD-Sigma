from rest_framework import serializers
<<<<<<< HEAD
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import (
    Taller, Usuario, Modulo, ModuloContratado,
    Tecnico, Repuesto, OrdenTrabajo, OrdenRepuesto,
    Comuna, Cliente, Vehiculo
)


class ComunaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comuna
        fields = '__all__'


class TallerSerializer(serializers.ModelSerializer):
    comuna_nombre = serializers.CharField(source='comuna.nombre', read_only=True, default=None)

=======
from .models import (
    Taller, Usuario, Modulo, ModuloContratado,
    Tecnico, Repuesto, OrdenTrabajo, OrdenRepuesto
)
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class TallerSerializer(serializers.ModelSerializer):
>>>>>>> 7e6817b1da587f52b1f6b667dee2846aa38e5665
    class Meta:
        model = Taller
        fields = '__all__'


<<<<<<< HEAD
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


=======
>>>>>>> 7e6817b1da587f52b1f6b667dee2846aa38e5665
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
<<<<<<< HEAD
        fields = ['id', 'username', 'email', 'rol', 'taller']

=======
        fields = ['id', 'username', 'email', 'rol', 'taller']   
>>>>>>> 7e6817b1da587f52b1f6b667dee2846aa38e5665

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['taller_id'] = user.taller_id
        token['rol'] = user.rol
        token['username'] = user.username
        return token

<<<<<<< HEAD

class TecnicoSerializer(serializers.ModelSerializer):
    nombre = serializers.SerializerMethodField()
    email = serializers.EmailField(source='usuario.email', read_only=True)
    telefono = serializers.CharField(source='usuario.telefono', read_only=True)
=======
class TecnicoSerializer(serializers.ModelSerializer):
    nombre = serializers.SerializerMethodField()
>>>>>>> 7e6817b1da587f52b1f6b667dee2846aa38e5665

    class Meta:
        model = Tecnico
        fields = '__all__'

    def get_nombre(self, obj):
        nombre_completo = f"{obj.usuario.first_name} {obj.usuario.last_name}".strip()
        return nombre_completo or obj.usuario.username

<<<<<<< HEAD

=======
>>>>>>> 7e6817b1da587f52b1f6b667dee2846aa38e5665
class TecnicoCreateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    nombre = serializers.CharField(write_only=True)
    apellido = serializers.CharField(write_only=True, required=False, allow_blank=True)
<<<<<<< HEAD
    email = serializers.EmailField(write_only=True, required=False, allow_blank=True)
    telefono = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Tecnico
        fields = ['id', 'username', 'password', 'nombre', 'apellido', 'email', 'telefono', 'especialidad', 'eficiencia_promedio']
=======

    class Meta:
        model = Tecnico
        fields = ['id', 'username', 'password', 'nombre', 'apellido', 'especialidad', 'eficiencia_promedio']
>>>>>>> 7e6817b1da587f52b1f6b667dee2846aa38e5665

    def create(self, validated_data):
        username = validated_data.pop('username')
        password = validated_data.pop('password')
        nombre = validated_data.pop('nombre')
        apellido = validated_data.pop('apellido', '')
<<<<<<< HEAD
        email = validated_data.pop('email', '')
        telefono = validated_data.pop('telefono', '')
        
        taller = self.context['request'].user.taller
        usuario = Usuario.objects.create_user(
            username=username, password=password, rol='tecnico', taller=taller,
            first_name=nombre, last_name=apellido, email=email, telefono=telefono
        )
        return Tecnico.objects.create(usuario=usuario, taller=taller, **validated_data)


=======
        taller = self.context['request'].user.taller
        usuario = Usuario.objects.create_user(
            username=username, password=password, rol='tecnico', taller=taller,
            first_name=nombre, last_name=apellido
        )
        return Tecnico.objects.create(usuario=usuario, taller=taller, **validated_data)

>>>>>>> 7e6817b1da587f52b1f6b667dee2846aa38e5665
class RepuestoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Repuesto
        fields = '__all__'
        read_only_fields = ['taller']

<<<<<<< HEAD

class ClienteSerializer(serializers.ModelSerializer):
    comuna_nombre = serializers.CharField(source='comuna.nombre', read_only=True, default=None)

    class Meta:
        model = Cliente
        fields = '__all__'
        read_only_fields = ['taller']


class VehiculoSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source='cliente.nombre', read_only=True)

    class Meta:
        model = Vehiculo
        fields = '__all__'


class OrdenRepuestoSerializer(serializers.ModelSerializer):
    repuesto_nombre = serializers.CharField(source='repuesto.nombre', read_only=True)
    repuesto_precio = serializers.DecimalField(source='repuesto.precio', read_only=True, max_digits=10, decimal_places=2)

    class Meta:
        model = OrdenRepuesto
        fields = '__all__'


class OrdenTrabajoSerializer(serializers.ModelSerializer):
    tecnico_nombre = serializers.SerializerMethodField()
    cliente_nombre = serializers.SerializerMethodField()
    cliente_telefono = serializers.SerializerMethodField()
    equipo = serializers.SerializerMethodField()
    patente = serializers.CharField(source='vehiculo.patente', read_only=True)
    repuestos_usados = OrdenRepuestoSerializer(many=True, read_only=True)

    class Meta:
        model = OrdenTrabajo
        fields = '__all__'
        read_only_fields = ['taller']

    def get_tecnico_nombre(self, obj):
        if not obj.tecnico:
            return None
        nombre_completo = f"{obj.tecnico.usuario.first_name} {obj.tecnico.usuario.last_name}".strip()
        return nombre_completo or obj.tecnico.usuario.username

    def get_cliente_nombre(self, obj):
        return obj.vehiculo.cliente.nombre if obj.vehiculo_id else None

    def get_cliente_telefono(self, obj):
        return obj.vehiculo.cliente.telefono if obj.vehiculo_id else None

    def get_equipo(self, obj):
        if not obj.vehiculo_id:
            return None
        partes = [obj.vehiculo.modelo, obj.vehiculo.patente]
        return ' — '.join([p for p in partes if p])


class OrdenTrabajoCreateSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(write_only=True)
    cliente_rut = serializers.CharField(write_only=True, required=False, allow_blank=True)
    cliente_telefono = serializers.CharField(write_only=True, required=False, allow_blank=True)
    cliente_email = serializers.CharField(write_only=True, required=False, allow_blank=True)
    vehiculo_patente = serializers.CharField(write_only=True)
    vehiculo_modelo = serializers.CharField(write_only=True, required=False, allow_blank=True)
    vehiculo_anio = serializers.IntegerField(write_only=True, required=False, allow_null=True)
=======
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
    cliente_direccion = serializers.CharField(source='cliente.direccion', read_only=True)
    tecnico_nombre = serializers.CharField(source='tecnico.usuario.username', read_only=True)
    repuestos_usados = OrdenRepuestoSerializer(many=True, read_only=True) 
>>>>>>> 7e6817b1da587f52b1f6b667dee2846aa38e5665

    class Meta:
        model = OrdenTrabajo
        fields = [
<<<<<<< HEAD
            'id', 'tecnico', 'descripcion_problema', 'estado',
            'cliente_nombre', 'cliente_rut', 'cliente_telefono', 'cliente_email',
            'vehiculo_patente', 'vehiculo_modelo', 'vehiculo_anio',
        ]

    def create(self, validated_data):
        taller = self.context['request'].user.taller

        cliente_nombre = validated_data.pop('cliente_nombre')
        cliente_rut = validated_data.pop('cliente_rut', '')
        cliente_telefono = validated_data.pop('cliente_telefono', '')
        cliente_email = validated_data.pop('cliente_email', '')
        vehiculo_patente = validated_data.pop('vehiculo_patente').upper().strip()
        vehiculo_modelo = validated_data.pop('vehiculo_modelo', '')
        vehiculo_anio = validated_data.pop('vehiculo_anio', None)

        if cliente_rut:
            cliente, created = Cliente.objects.get_or_create(
                taller=taller, rut=cliente_rut,
                defaults={'nombre': cliente_nombre, 'telefono': cliente_telefono, 'email': cliente_email},
            )
            if not created:
                cliente.nombre = cliente_nombre
                if cliente_telefono:
                    cliente.telefono = cliente_telefono
                if cliente_email:
                    cliente.email = cliente_email
                cliente.save()
        else:
            cliente = Cliente.objects.create(
                taller=taller, nombre=cliente_nombre,
                telefono=cliente_telefono, email=cliente_email,
            )

        vehiculo, created = Vehiculo.objects.get_or_create(
            patente=vehiculo_patente,
            defaults={'cliente': cliente, 'modelo': vehiculo_modelo, 'anio': vehiculo_anio},
        )
        if not created:
            vehiculo.cliente = cliente
            if vehiculo_modelo:
                vehiculo.modelo = vehiculo_modelo
            if vehiculo_anio:
                vehiculo.anio = vehiculo_anio
            vehiculo.save()

        return OrdenTrabajo.objects.create(taller=taller, vehiculo=vehiculo, **validated_data)
=======
            'id', 'taller', 'codigo_seguimiento', 'tecnico', 'tecnico_nombre',
            'cliente', 'cliente_nombre', 'cliente_email', 'cliente_telefono', 'cliente_direccion',
            'equipo', 'patente', 'descripcion_problema', 'estado', 'fecha_recepcion', 'repuestos_usados'
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
>>>>>>> 7e6817b1da587f52b1f6b667dee2846aa38e5665
