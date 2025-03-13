# email_sender.py
import requests
from config import MAUTIC_BASE_URL, MAUTIC_USERNAME, MAUTIC_PASSWORD, EMAIL_TEMPLATE_ID

def get_contacts_with_climabulletin():
    """
    Obtiene los contactos que tienen el campo 'climabulletin' establecido en verdadero.
    """
    url = f"{MAUTIC_BASE_URL}/api/contacts?search=climabulletin:1"
    response = requests.get(url, auth=(MAUTIC_USERNAME, MAUTIC_PASSWORD))
    contacts = []
    if response.status_code == 200:
        data = response.json()
        contacts = list(data.get("contacts", {}).values())
    else:
        print(f"Error al obtener contactos: {response.text}")
    return contacts

def send_email_via_mautic(contact_id, email_template_id=EMAIL_TEMPLATE_ID):
    """
    Envía el boletín de clima a un contacto mediante el template de email configurado en Mautic.
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
    Consulta los contactos que tienen activado el boletín de clima y les envía el email.
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
