import json
import requests
from config import MAUTIC_BASE_URL, MAUTIC_USERNAME, MAUTIC_PASSWORD

# Mapeo de campos: clave = campo en Mautic, valor = campo en el JSON
field_mapping = {
    "firstname": "name",
    "lastname": "last_name",
    "email": "mail",
    "mobile": "phone_mobile",
    "mobilewithoutplus": "phone_mobile_withous_plus",
    "forecastbulletin": "forecast_bulletin",
    "climabulletin": "clima_bulletin",
    "cities": "cities",
}

def get_contact_by_mail(mail):
    url = f"{MAUTIC_BASE_URL}/api/contacts?where[0][col]=email&where[0][expr]=eq&where[0][val]={mail}"
    try:
        response = requests.get(url, auth=(MAUTIC_USERNAME, MAUTIC_PASSWORD))
        response.raise_for_status()
        data = response.json()
        contacts = data.get("contacts", {})
        if contacts:
            first_contact = next(iter(contacts.values()))
            return first_contact
    except requests.RequestException as e:
        print(f"Error al buscar contacto por mail: {e}")
    return None

def extract_field(contact, field):
    fields = contact.get("fields", {})
    core_val = fields.get("core", {}).get(field, {}).get("value")
    if core_val is not None:
        return core_val
    return fields.get("custom", {}).get(field, {}).get("value")

def normalize_value(field, value):
    # Para el campo "cities": si es un array, unir sus valores con "-"
    if field == "cities":
        if isinstance(value, list):
            return "-".join(str(city).strip() for city in value)
        return str(value).strip() if value is not None else ""
    
    # Normalización para campos booleanos
    if field in ["forecastbulletin", "climabulletin"]:
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return value == 1
        if isinstance(value, str):
            val = value.strip().lower()
            if val in ['true', '1', 'yes']:
                return True
            elif val in ['false', '0', 'no']:
                return False
            return val
        return False
    if value is None:
        return ""
    return str(value).strip()

def update_contact_in_mautic(contact_id, update_data):
    url = f"{MAUTIC_BASE_URL}/api/contacts/{contact_id}/edit"
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.patch(url, json=update_data, auth=(MAUTIC_USERNAME, MAUTIC_PASSWORD), headers=headers)
        response.raise_for_status()
        print(f"Contacto {contact_id} actualizado con: {update_data}")
        return contact_id
    except requests.RequestException as e:
        print(f"Error al actualizar contacto {contact_id}: {e}")
        return None

def create_contact_in_mautic(new_contact):
    url = f"{MAUTIC_BASE_URL}/api/contacts/new"
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(url, json=new_contact, auth=(MAUTIC_USERNAME, MAUTIC_PASSWORD), headers=headers)
        response.raise_for_status()
        contact_info = response.json().get("contact", {})
        contact_id = contact_info.get("id")
        print(f"Contacto creado: {new_contact['email']} (ID: {contact_id})")
        return contact_id
    except requests.RequestException as e:
        print(f"Error al crear contacto {new_contact.get('email')}: {e}")
        return None

def process_contact(json_contact, stats):
    # Construir el nuevo contacto con valores normalizados
    new_contact_data = {}
    for mautic_field, json_field in field_mapping.items():
        raw_value = json_contact.get(json_field)
        new_contact_data[mautic_field] = normalize_value(mautic_field, raw_value)
    
    mail = new_contact_data.get("email")
    if not mail:
        print("No se encontró correo, omitiendo contacto.")
        stats["error"] += 1
        return
    
    existing_contact = get_contact_by_mail(mail)
    if existing_contact:
        differences = {}
        for mautic_field, json_field in field_mapping.items():
            new_value = normalize_value(mautic_field, json_contact.get(json_field))
            existing_value = normalize_value(mautic_field, extract_field(existing_contact, mautic_field))
            if new_value != existing_value:
                differences[mautic_field] = new_value
        if differences:
            contact_id = existing_contact.get("id")
            updated_id = update_contact_in_mautic(contact_id, differences)
            if updated_id:
                stats["updated"] += 1
            else:
                stats["error"] += 1
        else:
            print(f"Contacto con correo {mail} ya está actualizado; no se requiere acción.")
            stats["existing"] += 1
    else:
        new_id = create_contact_in_mautic(new_contact_data)
        if new_id:
            stats["created"] += 1
        else:
            stats["error"] += 1

def etl_import_contacts():
    stats = {
        "created": 0,
        "updated": 0,
        "existing": 0,
        "error": 0
    }
    
    users_file = 'users.json'

    with open(users_file, 'r', encoding='utf-8') as file:
        contacts = json.load(file)
        for contact in contacts:
            process_contact(contact, stats)
    
    print("\nResumen del proceso ETL:")
    print(f"Contactos creados: {stats['created']}")
    print(f"Contactos actualizados: {stats['updated']}")
    print(f"Contactos sin cambios: {stats['existing']}")
    print(f"Contactos con error: {stats['error']}")
