import json
import requests
import urllib.parse

# Configuración de la API de Mautic
MAUTIC_BASE_URL = 'http://localhost:8080'  # URL de tu instancia de Mautic
MAUTIC_USERNAME = 'mautic'                # Usuario configurado para la API en Mautic
MAUTIC_PASSWORD = 'Khiara1919;'           # Contraseña para la API

# Mapeo de campos: clave = campo en Mautic, valor = campo en el JSON
field_mapping = {
    "firstname": "name",
    "lastname": "last_name",
    "email": "mail",
    "mobile": "phone_mobile",
    "forecastbulletin": "forecast_bulletin",
    "climabulletin": "clima_bulletin",
    "city": "primary_address_city"
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

def get_segment_by_name(segment_name):
    """
    Busca en Mautic si ya existe un segmento con el nombre dado.
    Retorna el ID del segmento si lo encuentra o None en caso contrario.
    """
    url = f"{MAUTIC_BASE_URL}/api/segments"
    try:
        response = requests.get(url, auth=(MAUTIC_USERNAME, MAUTIC_PASSWORD))
        response.raise_for_status()
        data = response.json()
        lists_data = data.get("lists", [])
        if isinstance(lists_data, dict):
            segments = list(lists_data.values())
        else:
            segments = lists_data  
        for seg in segments:
            if seg.get("name") == segment_name:
                return seg.get("id")
    except requests.RequestException as e:
        print(f"Error al obtener segmentos: {e}")
    return None

def create_segment(segment_name):
    url = f"{MAUTIC_BASE_URL}/api/segments/new"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "name": segment_name,
        "description": "Segmento de contactos interesados en el boletín de clima"
    }
    try:
        response = requests.post(url, json=payload, auth=(MAUTIC_USERNAME, MAUTIC_PASSWORD), headers=headers)
        response.raise_for_status()
        segment_info = response.json().get("list", {})
        segment_id = segment_info.get("id")
        print(f"Segmento creado: {segment_name} (ID: {segment_id})")
        return segment_id
    except requests.RequestException as e:
        print(f"Error al crear segmento {segment_name}: {e}")
        return None

def add_contact_to_segment(segment_id, contact_id):
    url = f"{MAUTIC_BASE_URL}/api/segments/{segment_id}/contact/{contact_id}/add"
    try:
        response = requests.post(url, auth=(MAUTIC_USERNAME, MAUTIC_PASSWORD))
        response.raise_for_status()
        print(f"Contacto {contact_id} agregado al segmento {segment_id}")
        return True
    except requests.RequestException as e:
        print(f"Error al agregar contacto {contact_id} al segmento {segment_id}: {e}")
        return False

def process_contact(json_contact, stats, clima_contacts):
    new_contact_data = {}
    for mautic_field, json_field in field_mapping.items():
        new_contact_data[mautic_field] = json_contact.get(json_field)
    
    mail = new_contact_data.get("email")
    if not mail:
        print("No se encontró correo, omitiendo contacto.")
        stats["error"] += 1
        return
    
    # Verificar si el contacto está interesado en el boletín de clima
    interested = normalize_value("climabulletin", new_contact_data.get("climabulletin"))
    
    existing_contact = get_contact_by_mail(mail)
    if existing_contact:
        differences = {}
        for mautic_field, json_field in field_mapping.items():
            new_value = json_contact.get(json_field)
            existing_value = extract_field(existing_contact, mautic_field)
            norm_new = normalize_value(mautic_field, new_value)
            norm_existing = normalize_value(mautic_field, existing_value)
            if norm_new != norm_existing:
                differences[mautic_field] = new_value
        if differences:
            contact_id = existing_contact.get("id")
            updated_id = update_contact_in_mautic(contact_id, differences)
            if updated_id:
                stats["updated"] += 1
                if interested is True:
                    clima_contacts.append(updated_id)
            else:
                stats["error"] += 1
        else:
            print(f"Contacto con correo {mail} ya está actualizado; no se requiere acción.")
            stats["existing"] += 1
            if interested is True:
                clima_contacts.append(existing_contact.get("id"))
    else:
        new_id = create_contact_in_mautic(new_contact_data)
        if new_id:
            stats["created"] += 1
            if interested is True:
                clima_contacts.append(new_id)
        else:
            stats["error"] += 1

def etl_import_contacts(json_file):
    stats = {
        "created": 0,
        "updated": 0,
        "existing": 0,
        "error": 0
    }
    
    # Lista para almacenar los IDs de contactos interesados en el boletín de clima
    clima_contacts = []
    
    with open(json_file, 'r', encoding='utf-8') as file:
        contacts = json.load(file)
        for contact in contacts:
            process_contact(contact, stats, clima_contacts)
    
    print("\nResumen del proceso ETL:")
    print(f"Contactos creados: {stats['created']}")
    print(f"Contactos actualizados: {stats['updated']}")
    print(f"Contactos sin cambios: {stats['existing']}")
    print(f"Contactos con error: {stats['error']}")
    
    # Solo se procede si existen contactos interesados nuevos para agregar
    if clima_contacts:
        segment_name = "Interesados en boletin de clima"
        # Primero verifica si ya existe un segmento con ese nombre
        segment_id = get_segment_by_name(segment_name)
        if segment_id:
            print(f"El segmento '{segment_name}' ya existe (ID: {segment_id}). Se agregarán los nuevos contactos.")
        else:
            segment_id = create_segment(segment_name)
        if segment_id:
            for contact_id in clima_contacts:
                add_contact_to_segment(segment_id, contact_id)
        else:
            print("No se pudo obtener o crear el segmento.")
    else:
        print("No hay contactos nuevos interesados en el boletín de clima para agregar al segmento.")

if __name__ == "__main__":
    etl_import_contacts('users.json')
