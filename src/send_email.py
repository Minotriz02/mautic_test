import requests

# Configuración de la API de Mautic
MAUTIC_BASE_URL = 'http://localhost:8080'  # URL de tu instancia de Mautic
MAUTIC_USERNAME = 'mautic'                 # Usuario configurado para la API en Mautic
MAUTIC_PASSWORD = 'Khiara1919;'            # Contraseña para la API

# ID del template de email configurado en Mautic para el boletín de clima
EMAIL_TEMPLATE_ID = 1  # Ajusta este valor al ID correcto de tu template

def get_contacts_with_climabulletin():
    """
    Obtiene los contactos que tienen el campo 'climabulletin' establecido en verdadero.
    Se utiliza el parámetro 'search' de la API para filtrar.
    Asegúrate de que el alias del campo en Mautic sea 'climabulletin' o, si tiene otro alias
    (por ejemplo, "c_climabulletin"), actualiza el parámetro en la URL.
    """
    url = f"{MAUTIC_BASE_URL}/api/contacts?search=climabulletin:1"
    response = requests.get(url, auth=(MAUTIC_USERNAME, MAUTIC_PASSWORD))
    contacts = []
    if response.status_code == 200:
        data = response.json()
        # La API retorna los contactos en un diccionario; convertimos a lista.
        contacts = list(data.get("contacts", {}).values())
    else:
        print(f"Error al obtener contactos: {response.text}")
    return contacts

def send_email_via_mautic(contact_id, email_template_id=EMAIL_TEMPLATE_ID):
    """
    Envía el boletín de clima a un contacto mediante el template configurado en Mautic.
    Se utiliza el endpoint:
      /api/emails/{template_id}/contact/{contact_id}/send

    Importante: El email template en Mautic debe estar configurado para usar tokens de personalización,
    por ejemplo:
      - En el contenido: usar {contactfield=city} para mostrar la ubicación del usuario.
      - En el subject: incluir {contactfield=firstname} para agregar el nombre del usuario.
    """
    url = f"{MAUTIC_BASE_URL}/api/emails/{email_template_id}/contact/{contact_id}/send"
    response = requests.post(url, auth=(MAUTIC_USERNAME, MAUTIC_PASSWORD))
    if response.status_code == 200:
        print(f"Email enviado al contacto {contact_id}")
        return True
    else:
        print(f"Error al enviar email al contacto {contact_id}: {response.text}")
        return False

def send_weather_emails():
    """
    Consulta los contactos que tienen activado el boletín de clima (climabulletin=true) y les envía el email.
    Al finalizar, muestra un resumen del envío.
    """
    contacts = get_contacts_with_climabulletin()
    sent_count = 0
    error_count = 0

    if not contacts:
        print("No se encontraron contactos con boletín de clima activado.")
        return

    for contact in contacts:
        contact_id = contact.get("id")
        if send_email_via_mautic(contact_id):
            sent_count += 1
        else:
            error_count += 1

    # Resumen final
    print("\nResumen del envío de boletines de clima:")
    print(f"Emails enviados: {sent_count}")
    print(f"Errores: {error_count}")

if __name__ == "__main__":
    send_weather_emails()
