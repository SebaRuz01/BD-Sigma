import os
import requests
from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # Tus importaciones originales
        import core.signals

        # --- Nuevo código para avisar a Discord ---
        webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
        
        if webhook_url:
            mensaje = {
                "content": "✅ **¡Deploy exitoso!** El servidor BD-Sigma acaba de actualizarse y está listo."
            }
            try:
                # Envía el mensaje al canal de Discord
                requests.post(webhook_url, json=mensaje)
            except Exception as e:
                print(f"Error al enviar notificación a Discord: {e}")
