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
    comuna_nombre = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    comuna_region = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Taller
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['comuna_nombre'] = instance.comuna.nombre if instance.comuna else ''
        data['comuna_region'] = instance.comuna.region if instance.comuna else ''
        return data

    def update(self, instance, validated_data):
        c_nombre = validated_data.pop('comuna_nombre', None)
        c_region = validated_data.pop('comuna_region', None)
        
        if c_nombre is not None:
            if c_nombre.strip() == '':
                instance.comuna = None
            else:
                comuna, _ = Comuna.objects.get_or_create(
                    nombre=c_nombre.strip(), 
                    defaults={'region': (c_region or 'Sin especificar').strip()}
                )
                instance.comuna = comuna

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

        request = self.context.get('request')
        origen = request.data.get('origen', 'web') if request else 'web'

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
        ordenes = bajo.objects.filter(tecnico=obj, vehiculo__isnull=False).select_related('vehiculo', 'vehiculo__cliente')
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
    
    vehiculo_anio = serializers.IntegerField(source='vehiculo.anio', read_only=True, default=None)
    
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
    # Campos del cliente enviados desde el formulario de React
    cliente_nombre = serializers.CharField(write_only=True, required=False, allow_blank=True)
    cliente_rut = serializers.CharField(write_only=True, required=False, allow_blank=True)
    cliente_email = serializers.EmailField(write_only=True, required=False, allow_blank=True)
    cliente_telefono = serializers.CharField(write_only=True, required=False, allow_blank=True)
    cliente_calle = serializers.CharField(write_only=True, required=False, allow_blank=True)
    cliente_numero = serializers.CharField(write_only=True, required=False, allow_blank=True)
    cliente_region = serializers.CharField(write_only=True, required=False, allow_blank=True)
    cliente_comuna = serializers.CharField(write_only=True, required=False, allow_blank=True)

    # Campos del vehículo enviados desde el formulario de React
    marca = serializers.CharField(write_only=True, required=False, allow_blank=True)
    modelo = serializers.CharField(write_only=True, required=False, allow_blank=True)
    vehiculo_patente = serializers.CharField(write_only=True, required=False, allow_blank=True)
    vehiculo_anio = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = OrdenTrabajo
        fields = '__all__'
        extra_kwargs = {
            'taller': {'required': False},
            'vehiculo': {'required': False},
        }

    def create(self, validated_data):
        request = self.context.get('request')
        
        # 1. Asignar taller automáticamente
        taller = None
        if request and hasattr(request, 'user') and request.user.taller:
            taller = request.user.taller
            validated_data['taller'] = taller

        # 2. Extraer datos del cliente
        c_nombre = validated_data.pop('cliente_nombre', '')
        c_rut = validated_data.pop('cliente_rut', '')
        c_email = validated_data.pop('cliente_email', '')
        c_telefono = validated_data.pop('cliente_telefono', '')
        c_calle = validated_data.pop('cliente_calle', '')
        c_numero = validated_data.pop('cliente_numero', '')
        c_region = validated_data.pop('cliente_region', '')
        c_comuna = validated_data.pop('cliente_comuna', '')

        # 3. Extraer datos del vehículo
        marca = validated_data.pop('marca', '')
        modelo_seleccionado = validated_data.pop('modelo', '')
        patente = validated_data.pop('vehiculo_patente', '')
        anio = validated_data.pop('vehiculo_anio', None)

        # 4. Gestionar Comuna del cliente
        comuna_obj = None
        if c_comuna:
            comuna_obj, _ = Comuna.objects.get_or_create(
                nombre=c_comuna.strip(),
                defaults={'region': (c_region or 'Sin especificar').strip()}
            )

        # 5. Crear o actualizar el Cliente
        cliente_obj = None
        if c_rut and taller:
            cliente_obj, _ = Cliente.objects.update_or_create(
                taller=taller,
                rut=c_rut.strip().upper(),
                defaults={
                    'nombre': c_nombre.strip(),
                    'email': c_email.strip(),
                    'telefono': c_telefono.strip(),
                    'calle': c_calle.strip(),
                    'numero': c_numero.strip(),
                    'comuna': comuna_obj,
                }
            )

        # 6. Unir marca y modelo en formato "MARCA - MODELO"
        if marca and modelo_seleccionado:
            modelo_final = f"{marca} - {modelo_seleccionado}"
        else:
            modelo_final = modelo_seleccionado or marca

        # 7. Crear o actualizar el Vehículo vinculado al cliente
        if patente:
            vehiculo_obj, _ = Vehiculo.objects.update_or_create(
                patente=patente.upper().strip(),
                defaults={
                    'modelo': modelo_final if modelo_final else None,
                    'anio': anio if anio else None,
                    'cliente': cliente_obj,
                }
            )
            validated_data['vehiculo'] = vehiculo_obj

        # Limpiar campos temporales por seguridad
        for campo in ['cliente_nombre', 'cliente_rut', 'cliente_email', 'cliente_telefono', 
                      'cliente_calle', 'cliente_numero', 'cliente_region', 'cliente_comuna',
                      'marca', 'modelo', 'vehiculo_patente', 'vehiculo_anio']:
            validated_data.pop(campo, None)

        return super().create(validated_data)


class CitaSerializer(serializers.ModelSerializer):
    taller_id = serializers.PrimaryKeyRelatedField(source='taller', queryset=Taller.objects.all())
    patente = serializers.CharField(write_only=True, required=False, allow_blank=True)
    modelo_vehiculo = serializers.CharField(write_only=True, required=False, allow_blank=True)

    taller_nombre = serializers.CharField(source='taller.nombre_comercial', read_only=True)
    cliente_nombre = serializers.CharField(source='cliente.nombre', read_only=True)
    vehiculo_patente = serializers.CharField(source='vehiculo.patente', read_only=True, default=None)

    class Meta:
        model = Cita
        fields = [
            'id', 'fecha_hora', 'motivo', 'estado', 'fecha_creacion',
            'taller_id', 'taller_nombre', 'cliente_nombre', 'vehiculo_patente',
            'patente', 'modelo_vehiculo',
        ]
        read_only_fields = ['id', 'fecha_creacion']

    def create(self, validated_data):
        user = self.context['request'].user
        taller = validated_data['taller']
        patente = (validated_data.pop('patente', '') or '').upper().strip()
        modelo = (validated_data.pop('modelo_vehiculo', '') or '').strip()
        validated_data.pop('estado', None)  

        nombre = f"{user.first_name} {user.last_name}".strip() or user.username
        cliente, _ = Cliente.objects.get_or_create(
            taller=taller,
            rut=f"APP-{user.id}",
            defaults={
                'nombre': nombre,
                'email': user.email or '',
                'telefono': user.telefono or '',
            },
        )

        vehiculo = None
        if patente and patente != 'S/P':
            vehiculo = Vehiculo.objects.filter(patente=patente).first()
            if vehiculo is None:
                vehiculo = Vehiculo.objects.create(patente=patente, cliente=cliente, modelo=modelo)
            elif vehiculo.cliente_id != cliente.id:
                vehiculo = None

        if vehiculo is None and (modelo or patente):
            info = f"[Vehículo: {modelo or 'sin modelo'} {patente}]".replace('  ', ' ')
            validated_data['motivo'] = f"{info} {validated_data.get('motivo', '')}".strip()

        return Cita.objects.create(
            cliente=cliente, vehiculo=vehiculo, estado='pendiente', **validated_data
        )


class VehiculoCreateSerializer(serializers.ModelSerializer):
    marca = serializers.CharField(write_only=True, required=False)
    modelo_vehiculo = serializers.CharField(write_only=True, source='modelo', required=False)

    class Meta:
        model = Vehiculo
        fields = ['patente', 'marca', 'modelo_vehiculo', 'anio', 'cliente']

    def create(self, validated_data):
        marca = validated_data.pop('marca', '')
        modelo_seleccionado = validated_data.pop('modelo', '')
        
        if marca and modelo_seleccionado:
            modelo_final = f"{marca} - {modelo_seleccionado}"
        else:
            modelo_final = modelo_seleccionado or marca

        vehiculo = Vehiculo.objects.create(
            modelo=modelo_final,
            patente=validated_data.get('patente'),
            anio=validated_data.get('anio'),
            cliente=validated_data.get('cliente')
        )
        return vehiculo
