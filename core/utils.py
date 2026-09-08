import resend
from decouple import config

# Configura tu clave API de Resend usando variables de entorno o ponla directamente
resend.api_key = config('RESEND_API_KEY', default='TU_API_KEY_AQUÍ')

def enviar_correo_orden(destinatario, orden):
    params = {
        "from": "SIGMA Taller <onboarding@resend.dev>",
        "to": [destinatario],
        "subject": f"Actualización de tu vehículo - Orden OT-{orden.id}",
        "html": f"""
            <div style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
                <h2 style="color: #2563eb;">¡Hola, {orden.cliente_nombre}!</h2>
                <p>El estado de tu vehículo (<strong>{orden.equipo}</strong>) ha cambiado a:</p>
                <p style="font-size: 16px; font-weight: bold; color: #2563eb;">{orden.estado}</p>
                <hr style="border: none; border-top: 1px solid #eaeaea; margin: 20px 0;" />
                <p style="font-size: 12px; color: #666;">Puedes revisar el progreso en tiempo real desde el portal de clientes de SIGMA.</p>
            </div>
        """,
    }

    try:
        email = resend.Emails.send(params)
        return email
    except Exception as e:
        print(f"Error al enviar correo con Resend: {e}")
