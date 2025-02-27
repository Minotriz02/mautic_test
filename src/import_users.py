import json
import requests

# Configuración de la API de Mautic
MAUTIC_BASE_URL = 'http://localhost:8080'  # URL de tu instancia de Mautic
MAUTIC_USERNAME = 'mautic'                 # Usuario configurado para la API en Mautic
MAUTIC_PASSWORD = 'Khiara1919;'            # Contraseña para la API

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

def get_contact_by_phone(phone):
    """
    Busca un contacto en Mautic utilizando el campo 'mobile' (celular).
    Se utiliza el parámetro 'search' de la API para filtrar por mobile.
    """
    url = f"{MAUTIC_BASE_URL}/api/contacts?search=mobile:{phone}"
    response = requests.get(url, auth=(MAUTIC_USERNAME, MAUTIC_PASSWORD))
    if response.status_code == 200:
        data = response.json()
        contacts = data.get("contacts", {})
        if contacts:
            # Toma el primer contacto encontrado
            first_contact = next(iter(contacts.values()))
            return first_contact
    return None

def extract_field(contact, field):
    """
    Extrae el valor de un campo dado del contacto.
    Primero busca en 'core' y si no lo encuentra, en 'custom'.
    """
    fields = contact.get("fields", {})
    core_val = fields.get("core", {}).get(field, {}).get("value")
    if core_val is not None:
        return core_val
    return fields.get("custom", {}).get(field, {}).get("value")

def normalize_value(field, value):
    """
    Normaliza el valor para comparación.
    Para campos booleanos, convierte diversas representaciones a True/False.
    Para otros campos, devuelve el valor como cadena sin espacios adicionales.
    """
    if field in ["forecastbulletin", "climabulletin"]:
        # Normalizar valores booleanos: 
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
            # Si no se reconoce, se devuelve como está
            return val
        return False
    # Para otros campos
    if value is None:
        return ""
    return str(value).strip()

def update_contact_in_mautic(contact_id, update_data):
    """
    Actualiza un contacto en Mautic con los datos proporcionados.
    Se utiliza el endpoint /api/contacts/{id}/edit con el método PATCH.
    Devuelve True si la actualización fue exitosa o False en caso de error.
    """
    url = f"{MAUTIC_BASE_URL}/api/contacts/{contact_id}/edit"
    headers = {'Content-Type': 'application/json'}
    response = requests.patch(url, json=update_data, auth=(MAUTIC_USERNAME, MAUTIC_PASSWORD), headers=headers)
    if response.status_code in [200, 204]:
        print(f"Contacto {contact_id} actualizado con: {update_data}")
        return True
    else:
        print(f"Error al actualizar contacto {contact_id}: {response.text}")
        return False

def create_contact_in_mautic(new_contact):
    """
    Crea un nuevo contacto en Mautic con los datos proporcionados.
    Considera códigos 200 y 201 como éxitos.
    Devuelve True si se creó correctamente o False en caso de error.
    """
    url = f"{MAUTIC_BASE_URL}/api/contacts/new"
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, json=new_contact, auth=(MAUTIC_USERNAME, MAUTIC_PASSWORD), headers=headers)
    
    if response.status_code in [200, 201]:
        contact_info = response.json().get("contact", {})
        contact_id = contact_info.get("id")
        print(f"Contacto creado: {new_contact['email']} (ID: {contact_id})")
        return True
    else:
        print(f"Error al crear contacto {new_contact.get('email')}: {response.text}")
        return False

def process_contact(json_contact, stats):
    """
    Procesa un único contacto:
      - Mapea los campos del JSON a los de Mautic.
      - Busca el contacto por celular.
      - Si existe, compara los campos y actualiza solo los que han cambiado.
      - Si no existe, crea el contacto.
    Actualiza las estadísticas en el diccionario 'stats'.
    """
    # Construir los datos para Mautic a partir del mapeo
    new_contact_data = {}
    for mautic_field, json_field in field_mapping.items():
        new_contact_data[mautic_field] = json_contact.get(json_field)
    
    phone = new_contact_data.get("mobile")
    if not phone:
        print("No se encontró número de celular, omitiendo contacto.")
        stats["error"] += 1
        return

    existing_contact = get_contact_by_phone(phone)
    if existing_contact:
        differences = {}
        # Comparar cada campo: se normalizan los valores antes de comparar
        for mautic_field, json_field in field_mapping.items():
            new_value = json_contact.get(json_field)
            existing_value = extract_field(existing_contact, mautic_field)
            norm_new = normalize_value(mautic_field, new_value)
            norm_existing = normalize_value(mautic_field, existing_value)
            if norm_new != norm_existing:
                differences[mautic_field] = new_value
        if differences:
            contact_id = existing_contact.get("id")
            if update_contact_in_mautic(contact_id, differences):
                stats["updated"] += 1
            else:
                stats["error"] += 1
        else:
            print(f"Contacto con móvil {phone} ya está actualizado; no se requiere acción.")
            stats["existing"] += 1
    else:
        if create_contact_in_mautic(new_contact_data):
            stats["created"] += 1
        else:
            stats["error"] += 1

def etl_import_contacts(json_file):
    """
    Proceso ETL: extrae los contactos del archivo JSON e importa (o actualiza) cada contacto en Mautic.
    Al finalizar, imprime un resumen de la operación.
    """
    # Estadísticas de procesamiento
    stats = {
        "created": 0,
        "updated": 0,
        "existing": 0,
        "error": 0
    }
    
    with open(json_file, 'r', encoding='utf-8') as file:
        contacts = json.load(file)
        for contact in contacts:
            process_contact(contact, stats)
    
    # Resumen final
    print("\nResumen del proceso ETL:")
    print(f"Contactos creados: {stats['created']}")
    print(f"Contactos actualizados: {stats['updated']}")
    print(f"Contactos sin cambios: {stats['existing']}")
    print(f"Contactos con error: {stats['error']}")

if __name__ == "__main__":
    etl_import_contacts('users.json')