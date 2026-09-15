from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    TallerViewSet, UsuarioViewSet,
    ModuloViewSet, ModuloContratadoViewSet,
    TecnicoViewSet, RepuestoViewSet,
    OrdenTrabajoViewSet, OrdenRepuestoViewSet,
    OrdenPublicaView, LoginClienteViewSet # <--- Importa también tu nuevo viewset aquí
)

router = DefaultRouter()
# Registramos todas las entidades en el mismo router
router.register(r'talleres', TallerViewSet)
router.register(r'usuarios', UsuarioViewSet)
router.register(r'modulos', ModuloViewSet)
router.register(r'modulos-contratados', ModuloContratadoViewSet)
router.register(r'tecnicos', TecnicoViewSet, basename='tecnico')
router.register(r'repuestos', RepuestoViewSet, basename='repuesto')
router.register(r'ordenes', OrdenTrabajoViewSet, basename='orden')
router.register(r'ordenes-repuestos', OrdenRepuestoViewSet)
router.register(r'logincliente', LoginClienteViewSet, basename='logincliente') # <--- La clave para la app móvil

# Unificamos todo bajo el prefijo 'api/' y agregamos la ruta pública
urlpatterns = [
    path('api/', include(router.urls)),
    path('api/publico/ordenes/<str:codigo>/', OrdenPublicaView.as_view()),
]
