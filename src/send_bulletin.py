import requests

# Configuración de la API de Mautic
MAUTIC_BASE_URL = 'http://localhost:8080'  # URL de tu instancia de Mautic
MAUTIC_USERNAME = 'mautic'                 # Usuario configurado para la API en Mautic
MAUTIC_PASSWORD = 'Khiara1919;'            # Contraseña para la API

# ID de los templates configurados en Mautic
EMAIL_TEMPLATE_ID = 1   # Ajusta este valor al ID correcto de tu template de email
SMS_TEMPLATE_ID   = 1   # Ajusta este valor al ID correcto de tu template SMS

def get_contacts_with_climabulletin():
    """
    Obtiene los contactos que tienen el campo 'climabulletin' establecido en verdadero.
    Se utiliza el parámetro 'search' de la API para filtrar.
    Asegúrate de que el alias del campo en Mautic sea 'climabulletin' (o actualízalo si es diferente).
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

# Envío de Email vía Mautic
def send_email_via_mautic(contact_id, email_template_id=EMAIL_TEMPLATE_ID):
    """
    Envía el boletín de clima a un contacto mediante el template de email configurado en Mautic.
    Se utiliza el endpoint:
      /api/emails/{template_id}/contact/{contact_id}/send
    El template debe incluir tokens para personalizar (por ejemplo, {contactfield=city} o {contactfield=firstname}).
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
        print("No se encontraron contactos con boletín de clima activado para email.")
        return

    for contact in contacts:
        contact_id = contact.get("id")
        if send_email_via_mautic(contact_id):
            sent_count += 1
        else:
            error_count += 1

    print("\nResumen del envío de boletines por Email:")
    print(f"Emails enviados: {sent_count}")
    print(f"Errores: {error_count}")

# Envío de SMS vía Mautic (usando integración con Twilio)
def send_sms_via_mautic(contact_id, sms_template_id=SMS_TEMPLATE_ID):
    """
    Envía un SMS a un contacto mediante el template SMS configurado en Mautic.
    Se utiliza el endpoint:
      /api/smses/{sms_template_id}/contact/{contact_id}/send
    Este endpoint funciona si ya has configurado en Mautic la integración con Twilio.
    """
    url = f"{MAUTIC_BASE_URL}/api/smses/{sms_template_id}/contact/{contact_id}/send"
    print(url)
    response = requests.get(url, auth=(MAUTIC_USERNAME, MAUTIC_PASSWORD))
    print(response.text)
    if response.status_code == 200:
        print(f"SMS enviado al contacto {contact_id}")
        return True
    else:
        print(f"Error al enviar SMS al contacto {contact_id}: {response.text}")
        return False

def send_sms_notifications():
    """
    Consulta los contactos que tienen activado el boletín de clima (climabulletin=true) y les envía un SMS.
    Al finalizar, muestra un resumen del envío.
    """
    contacts = get_contacts_with_climabulletin()
    sent_count = 0
    error_count = 0

    if not contacts:
        print("No se encontraron contactos con boletín de clima activado para SMS.")
        return

    for contact in contacts:
        contact_id = contact.get("id")
        if send_sms_via_mautic(contact_id):
            sent_count += 1
        else:
            error_count += 1

    print("\nResumen del envío de boletines por SMS:")
    print(f"SMS enviados: {sent_count}")
    print(f"Errores: {error_count}")

# Main que invoca el envío de email y SMS
def send_clima_bulletin():
    print("Iniciando el envío del boletín de clima...")
    print("\nEnviando boletín por Email:")
    send_weather_emails()
    print("\nEnviando boletín por SMS:")
    send_sms_notifications()

if __name__ == "__main__":
    send_clima_bulletin()
