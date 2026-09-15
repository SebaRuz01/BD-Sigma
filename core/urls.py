from django.urls import path, include  
from rest_framework.routers import DefaultRouter
from .views import (
    TallerViewSet, UsuarioViewSet,
    ModuloViewSet, ModuloContratadoViewSet,
    TecnicoViewSet, RepuestoViewSet,
    OrdenTrabajoViewSet, OrdenRepuestoViewSet,
    OrdenPublicaView, LoginClienteViewSet
)

router = DefaultRouter()
router.register(r'talleres', TallerViewSet)
router.register(r'usuarios', UsuarioViewSet)
router.register(r'modulos', ModuloViewSet)
router.register(r'modulos-contratados', ModuloContratadoViewSet)
router.register(r'tecnicos', TecnicoViewSet, basename='tecnico')
router.register(r'repuestos', RepuestoViewSet, basename='repuesto')
router.register(r'ordenes', OrdenTrabajoViewSet, basename='orden')
router.register(r'ordenes-repuestos', OrdenRepuestoViewSet)
router.register(r'logincliente', LoginClienteViewSet, basename='logincliente')

urlpatterns = [
    path('api/', include(router.urls)), # <--- Aquí es donde se usa 'include'
    path('api/publico/ordenes/<str:codigo>/', OrdenPublicaView.as_view()),
]
