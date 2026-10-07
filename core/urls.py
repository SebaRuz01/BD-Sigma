from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    TallerViewSet, UsuarioViewSet,
    ModuloViewSet, ModuloContratadoViewSet,
    TecnicoViewSet, RepuestoViewSet,
    OrdenTrabajoViewSet, OrdenRepuestoViewSet,
    ComunaViewSet, ClienteViewSet,PasswordResetRequestView, PasswordResetConfirmView, VehiculoViewSet,
    OrdenPublicaView, CitaViewSet, CalcularEstimacionIAView,
    EnviarCorreoEstimacionView,
)

router = DefaultRouter()
router.register(r'talleres', TallerViewSet)
router.register(r'usuarios', UsuarioViewSet)
router.register(r'modulos', ModuloViewSet)
router.register(r'modulos-contratados', ModuloContratadoViewSet)
router.register(r'ordenes-repuestos', OrdenRepuestoViewSet, basename='ordenrepuesto')
router.register(r'tecnicos', TecnicoViewSet, basename='tecnico')
router.register(r'repuestos', RepuestoViewSet, basename='repuesto')
router.register(r'ordenes', OrdenTrabajoViewSet, basename='orden')
router.register(r'comunas', ComunaViewSet)
router.register(r'clientes', ClienteViewSet, basename='cliente')
router.register(r'vehiculos', VehiculoViewSet, basename='vehiculo')
router.register(r'citas', CitaViewSet, basename='cita')




urlpatterns = router.urls + [
    path('publico/ordenes/<str:codigo>/', OrdenPublicaView.as_view()),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('ordenes/<int:pk>/estimar-ia/', CalcularEstimacionIAView.as_view()),
    path('ordenes/<int:pk>/enviar-correo/', EnviarCorreoEstimacionView.as_view()),
]
