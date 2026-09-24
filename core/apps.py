import os
import requests
from datetime import datetime
from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # Tus importaciones originales
        import core.signals

        webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
        # Si estás probando directo sin variable de entorno, usa:
        # webhook_url = "https://discord.com/api/webhooks/1552503024746766457/AyQWpvd2DGpqxQFQmdOij4L-TNa-e5RucSgNQZ3CdJiGKVqSSw62czHGO9A_1U_RSfDO"
        
        if webhook_url:
            # Capturamos los datos que Render provee automáticamente
            servicio = os.environ.get("RENDER_SERVICE_NAME", "BD-Sigma")
            commit = os.environ.get("RENDER_GIT_COMMIT", "Desconocido")[:7] # Cortamos a 7 caracteres para que sea legible
            rama = os.environ.get("RENDER_GIT_BRANCH", "main")
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Armamos el mensaje con formato "Embed" (tarjeta visual)
            mensaje = {
                "embeds": [
                    {
                        "title": "✅ Servidor Actualizado y En Línea",
                        "description": "El último deploy se ha completado correctamente.",
                        "color": 5763719,  # Código de color verde
                        "fields": [
                            {"name": "🖥️ Servicio", "value": servicio, "inline": True},
                            {"name": "🌿 Rama", "value": rama, "inline": True},
                            {"name": "📌 Commit", "value": f"`{commit}`", "inline": True},
                            {"name": "⏰ Hora de inicio", "value": fecha_actual, "inline": False}
                        ]
                    }
                ]
            }

            try:
                # Envía el mensaje al canal de Discord
                requests.post(webhook_url, json=mensaje)
            except Exception as e:
                print(f"Error al enviar notificación a Discord: {e}")
