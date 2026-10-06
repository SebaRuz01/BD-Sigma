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
    # Declaramos los campos explícitamente para que el PATCH no los ignore
    comuna_nombre = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    comuna_region = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Taller
        fields = '__all__'

    def to_representation(self, instance):
        # Al enviar datos al frontend, extraemos el texto de la relación
        data = super().to_representation(instance)
        data['comuna_nombre'] = instance.comuna.nombre if instance.comuna else ''
        data['comuna_region'] = instance.comuna.region if instance.comuna else ''
        return data

    def update(self, instance, validated_data):
        # Extraemos comuna_nombre y comuna_region de forma segura
        c_nombre = validated_data.pop('comuna_nombre', None)
        c_region = validated_data.pop('comuna_region', None)
        
        # Procesamos la creación/búsqueda en la BD
        if c_nombre is not None:
            if c_nombre.strip() == '':
                instance.comuna = None
            else:
                comuna, _ = Comuna.objects.get_or_create(
                    nombre=c_nombre.strip(), 
                    defaults={'region': (c_region or 'Sin especificar').strip()}
                )
                instance.comuna = comuna

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
                nombre=comuna_nombre.strip(), defaults={'region': (comuna_region or 'Sin especificar').strip()}
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
        model = Usuario
        fields = ['id', 'username', 'email', 'rol', 'taller', 'password', 'first_name', 'last_name', 'telefono']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        usuario = super().create(validated_data)
        
        if password:
            usuario.set_password(password)
            usuario.save()
            
        return usuario


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        # 1. Rescatamos el dato 'origen' que enviaremos desde el front (por defecto asumimos 'web' por seguridad)
        request = self.context.get('request')
        origen = request.data.get('origen', 'web') if request else 'web'

        # 2. REGLA DE BLOQUEO: Si es cliente y NO viene de la app -> Bloqueado
        if self.user.rol == 'cliente' and origen != 'mobile':
            raise AuthenticationFailed('Los clientes solo pueden iniciar sesión desde la App Móvil.')
        
        return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['taller_id'] = user.taller_id
        token['rol'] = user.rol
        token['username'] = user.username
        
        return token


class TecnicoSerializer(serializers.ModelSerializer):
    nombre = serializers.SerializerMethodField()
    email = serializers.EmailField(source='usuario.email', read_only=True)
    telefono = serializers.CharField(source='usuario.telefono', read_only=True)
    vehiculos = serializers.SerializerMethodField()

    class Meta:
        model = Tecnico
        fields = '__all__'

    def get_nombre(self, obj):
        nombre_completo = f"{obj.usuario.first_name} {obj.usuario.last_name}".strip()
        return nombre_completo or obj.usuario.username

    def get_vehiculos(self, obj):
        ordenes = OrdenTrabajo.objects.filter(tecnico=obj, vehiculo__isnull=False).select_related('vehiculo', 'vehiculo__cliente')
        vehiculos_lista = []
        patentes_vistas = set()
        
        for orden in ordenes:
            vehiculo = orden.vehiculo
            if vehiculo and vehiculo.patente not in patentes_vistas:
                patentes_vistas.add(vehiculo.patente)
                cliente_nombre = "Sin nombre"
                if vehiculo.cliente and vehiculo.cliente.nombre:
                    cliente_nombre = vehiculo.cliente.nombre
                
                vehiculos_lista.append({
                    'patente': vehiculo.patente,
                    'modelo': vehiculo.modelo or 'Vehículo',
                    'cliente_nombre': cliente_nombre
                })
        return vehiculos_lista


class TecnicoCreateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    nombre = serializers.CharField(write_only=True)
    apellido = serializers.CharField(write_only=True, required=False, allow_blank=True)
    email = serializers.EmailField(write_only=True, required=False, allow_blank=True)
    telefono = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Tecnico
        fields = ['id', 'username', 'password', 'nombre', 'apellido', 'email', 'telefono', 'especialidad', 'eficiencia_promedio']

    def create(self, validated_data):
        username = validated_data.pop('username')
        password = validated_data.pop('password')
        nombre = validated_data.pop('nombre')
        apellido = validated_data.pop('apellido', '')
        email = validated_data.pop('email', '')
        telefono = validated_data.pop('telefono', '')
        
        taller = self.context['request'].user.taller
        usuario = Usuario.objects.create_user(
            username=username, password=password, rol='tecnico', taller=taller,
            first_name=nombre, last_name=apellido, email=email, telefono=telefono
        )
        return Tecnico.objects.create(usuario=usuario, taller=taller, **validated_data)


class RepuestoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Repuesto
        fields = '__all__'
        read_only_fields = ['taller']


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

    class Meta:
        model = OrdenTrabajo
        fields = [
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


class CitaSerializer(serializers.ModelSerializer):
    taller_id = serializers.PrimaryKeyRelatedField(source='taller', queryset=Taller.objects.all())
    patente = serializers.CharField(write_only=True, required=False, allow_blank=True)
    modelo_vehiculo = serializers.CharField(write_only=True, required=False, allow_blank=True)

    taller_nombre = serializers.CharField(source='taller.nombre_comercial', read_only=True)
    cliente_nombre = serializers.CharField(source='cliente.nombre', read_only=True)
    vehiculo_patente = serializers.CharField(source='vehiculo.patente', read_only
