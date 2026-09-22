from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    TallerViewSet, UsuarioViewSet,
    ModuloViewSet, ModuloContratadoViewSet,
    TecnicoViewSet, RepuestoViewSet,
    OrdenTrabajoViewSet, OrdenRepuestoViewSet,
<<<<<<< HEAD
    ComunaViewSet, ClienteViewSet, VehiculoViewSet,
=======
>>>>>>> 7e6817b1da587f52b1f6b667dee2846aa38e5665
    OrdenPublicaView
)

router = DefaultRouter()
router.register(r'talleres', TallerViewSet)
router.register(r'usuarios', UsuarioViewSet)
router.register(r'modulos', ModuloViewSet)
router.register(r'modulos-contratados', ModuloContratadoViewSet)
<<<<<<< HEAD
router.register(r'ordenes-repuestos', OrdenRepuestoViewSet, basename='ordenrepuesto')
router.register(r'tecnicos', TecnicoViewSet, basename='tecnico')
router.register(r'repuestos', RepuestoViewSet, basename='repuesto')
router.register(r'ordenes', OrdenTrabajoViewSet, basename='orden')
router.register(r'comunas', ComunaViewSet)
router.register(r'clientes', ClienteViewSet, basename='cliente')
router.register(r'vehiculos', VehiculoViewSet, basename='vehiculo')
=======
router.register(r'ordenes-repuestos', OrdenRepuestoViewSet)
router.register(r'tecnicos', TecnicoViewSet, basename='tecnico')
router.register(r'repuestos', RepuestoViewSet, basename='repuesto')
router.register(r'ordenes', OrdenTrabajoViewSet, basename='orden')
>>>>>>> 7e6817b1da587f52b1f6b667dee2846aa38e5665

urlpatterns = router.urls + [
    path('publico/ordenes/<str:codigo>/', OrdenPublicaView.as_view()),
]
