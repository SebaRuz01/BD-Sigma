from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import OrdenTrabajo


@receiver(post_save, sender=OrdenTrabajo)
def orden_actualizada_signal(sender, instance, **kwargs):
    channel_layer = get_channel_layer()
    tecnico_nombre = None
    if instance.tecnico:
        nombre_completo = f"{instance.tecnico.usuario.first_name} {instance.tecnico.usuario.last_name}".strip()
        tecnico_nombre = nombre_completo or instance.tecnico.usuario.username

    async_to_sync(channel_layer.group_send)(
        f'orden_{instance.id}',
        {
            'type': 'orden_actualizada',
            'estado': instance.estado,
            'tecnico_nombre': tecnico_nombre,
        }
    )