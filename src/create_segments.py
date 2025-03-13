import requests
from config import MAUTIC_BASE_URL, MAUTIC_USERNAME, MAUTIC_PASSWORD

def get_all_contacts():
    """
    Obtiene todos los contactos desde Mautic.
    """
    url = f"{MAUTIC_BASE_URL}/api/contacts"
    try:
        response = requests.get(url, auth=(MAUTIC_USERNAME, MAUTIC_PASSWORD))
        response.raise_for_status()
        data = response.json()
        contacts = data.get("contacts", {})
        return contacts.values()
    except requests.RequestException as e:
        print(f"Error al obtener contactos: {e}")
        return []

def extract_field(contact, field):
    """
    Extrae el valor de un campo desde la estructura de contacto.
    """
    fields = contact.get("fields", {})
    core_val = fields.get("core", {}).get(field, {}).get("value")
    if core_val is not None:
        return core_val
    return fields.get("custom", {}).get(field, {}).get("value")

def normalize_value(field, value):
    """
    Normaliza el valor de un campo.
      - Para 'climabulletin': retorna True/False.
      - Para 'cities': se asume que ya es un string.
    """
    if field == "cities":
        return value.strip() if value else ""
    if field == "climabulletin":
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
        return False
    if value is None:
        return ""
    return str(value).strip()

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
    """
    Crea un nuevo segmento en Mautic con el nombre dado.
    """
    url = f"{MAUTIC_BASE_URL}/api/segments/new"
    headers = {'Content-Type': 'application/json'}
    # Se asume que la descripción usa el nombre de la ciudad extraído del segmento.
    city = segment_name.split(" - ")[1] if " - " in segment_name else segment_name
    payload = {
        "name": segment_name,
        "description": f"Segmento de contactos interesados en el clima de {city}"
    }
    try:
        response = requests.post(url, json=payload, auth=(MAUTIC_USERNAME, MAUTIC_PASSWORD), headers=headers)
        response.raise_for_status()
        segment_info = response.json().get("list", {})
        segment_id = segment_info.get("id")
        print(f"Segmento creado: {segment_name} (ID: {segment_id})")
        return segment_id
    except requests.RequestException as e:
        print(f"Error al crear segmento '{segment_name}': {e}")
        return None

def add_contact_to_segment(segment_id, contact_id):
    """
    Agrega el contacto al segmento utilizando el endpoint de Mautic.
    """
    url = f"{MAUTIC_BASE_URL}/api/segments/{segment_id}/contact/{contact_id}/add"
    try:
        response = requests.post(url, auth=(MAUTIC_USERNAME, MAUTIC_PASSWORD))
        response.raise_for_status()
        print(f"Contacto {contact_id} agregado al segmento {segment_id}")
        return True
    except requests.RequestException as e:
        print(f"Error al agregar contacto {contact_id} al segmento {segment_id}: {e}")
        return False

def process_segments():
    """
    Procesa todos los contactos, filtrando aquellos interesados en el boletín de clima,
    extrayendo las ciudades y asignándolos al segmento "Boletin clima - [nombre ciudad]".
    """
    contacts = get_all_contacts()
    for contact in contacts:
        contact_id = contact.get("id")
        raw_clima = extract_field(contact, "climabulletin")
        clima = normalize_value("climabulletin", raw_clima)
        if clima is True:
            # Obtener el campo cities (almacenado como string con separador "-")
            raw_cities = extract_field(contact, "cities")
            cities_str = normalize_value("cities", raw_cities)
            if cities_str:
                # Se asume que las ciudades están separadas por guiones ("-")
                city_list = [city.strip() for city in cities_str.split("-") if city.strip()]
                for city in city_list:
                    # Extraer solo el nombre de la ciudad (parte antes de la coma)
                    city_name = city.split(",")[0].strip() if "," in city else city
                    segment_name = f"Boletin clima - {city_name}"
                    # Verificar si el segmento ya existe, de lo contrario se crea
                    segment_id = get_segment_by_name(segment_name)
                    if not segment_id:
                        segment_id = create_segment(segment_name)
                    if segment_id:
                        add_contact_to_segment(segment_id, contact_id)
            else:
                print(f"Contacto {contact_id} no tiene ciudades definidas.")
        else:
            print(f"Contacto {contact_id} no está interesado en el boletin de clima.")
