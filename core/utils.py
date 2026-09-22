import resend
from decouple import config

resend.api_key = config('RESEND_API_KEY', default='TU_API_KEY_AQUÍ')


def enviar_correo_orden(orden):
    cliente = orden.vehiculo.cliente if (orden.vehiculo and orden.vehiculo.cliente) else None
    if not cliente or not cliente.email:
        return  # Sin correo registrado, no hay a quién enviarle

    equipo = f"{orden.vehiculo.modelo} — {orden.vehiculo.patente}".strip(' —')
    
    # Obtener el teléfono del técnico asignado de manera segura
    tecnico_telefono = 'No asignado'
    if orden.tecnico and orden.tecnico.usuario and hasattr(orden.tecnico.usuario, 'telefono') and orden.tecnico.usuario.telefono:
        tecnico_telefono = orden.tecnico.usuario.telefono

    params = {
        "from": "SIGMA Taller <onboarding@resend.dev>",
        "to": [cliente.email],
        "subject": f"Actualización de tu vehículo - Orden OT-{orden.id}",
        "html": f"""
            <div style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
                <h2 style="color: #2563eb;">¡Hola, {cliente.nombre}!</h2>
                <p>El estado de tu vehículo (<strong>{equipo}</strong>) ha cambiado a:</p>
                <p style="font-size: 16px; font-weight: bold; color: #2563eb;">{orden.estado}</p>
                <p>Teléfono de contacto del técnico asignado: <strong>{tecnico_telefono}</strong></p>
                <hr style="border: none; border-top: 1px solid #eaeaea; margin: 20px 0;" />
                <p style="font-size: 12px; color: #666;">Puedes revisar el progreso en tiempo real desde el portal de clientes de SIGMA usando tu código: <strong>{orden.codigo_seguimiento}</strong></p>
            </div>
        """,
    }

    try:
        email = resend.Emails.send(params)
        print(f"Correo enviado exitosamente vía Resend a {cliente.email}")
        return email
    except Exception as e:
        print(f"Error al enviar correo con Resend: {e}")