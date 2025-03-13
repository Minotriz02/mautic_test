import requests
from datetime import datetime
from bs4 import BeautifulSoup
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
    except Exception as e:
        print("Error al obtener contactos:", e)
        return []

def extract_field(contact, field):
    """
    Extrae el valor de un campo (buscando en 'core' y 'custom').
    """
    fields = contact.get("fields", {})
    core_val = fields.get("core", {}).get(field, {}).get("value")
    if core_val is not None:
        return core_val
    return fields.get("custom", {}).get(field, {}).get("value")

def get_unique_cities():
    """
    Extrae las ciudades únicas de los contactos.
    Se asume que el campo "cities" es un string con ciudades separadas por guiones.
    """
    contacts = get_all_contacts()
    unique_cities = set()
    for contact in contacts:
        raw_cities = extract_field(contact, "cities")
        if raw_cities:
            # Separa asumiendo que las ciudades vienen separadas por "-"
            cities = [c.strip() for c in raw_cities.split("-") if c.strip()]
            unique_cities.update(cities)
    return unique_cities

def get_lat_lon_from_city(city):
    """
    Utiliza Nominatim para obtener latitud y longitud de una ciudad.
    """
    url = "https://nominatim.openstreetmap.org/search.php"
    params = {"q": city, "format": "json"}
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, params=params, headers=headers)
        data = response.json()
        if data:
            return data[0]["lat"], data[0]["lon"]
    except Exception as e:
        print(f"Error al obtener coordenadas para {city}: {e}")
    return None, None

def get_weather_from_lat_lon(lat, lon):
    """
    Consulta la API de Open-Meteo para obtener la temperatura actual y la fecha.
    """
    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    try:
        response = requests.get(weather_url)
        if response.status_code == 200:
            weather_data = response.json()
            current = weather_data.get("current_weather", {})
            temperature = current.get("temperature")
            date_now = current.get("time")
            return temperature, date_now
    except Exception as e:
        print("Error al obtener clima:", e)
    return None, None

def format_date(date_str):
    """
    Convierte una fecha en formato ISO a dd-mm-yyyy.
    """
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.strftime("%d-%m-%Y")
    except Exception as e:
        print(f"Error al formatear la fecha '{date_str}':", e)
        return date_str

def generate_custom_sms(city, temperature, date_str):
    """
    Lee la plantilla base del sms y retorna el sms resultante.
    """
    formatted_date = format_date(date_str) if date_str else "Sin fecha"
    
    # Plantilla de SMS
    sms_template = f"""
    Hola {{contactfield=name}},
    El clima en {city} el dia de {formatted_date} es de {temperature}°C
    """    
    return sms_template

def get_sms_template_by_name(sms_name):
    """
    Busca en Mautic si ya existe un sms template con el nombre especificado.
    Retorna el ID del template si lo encuentra, o None en caso contrario.
    Se consulta usando el campo "name" directamente, tal como se muestra en la respuesta de la API.
    """
    url = f"{MAUTIC_BASE_URL}/api/smses?where[0][col]=name&where[0][expr]=eq&where[0][val]={sms_name}"
    try:
        response = requests.get(url, auth=(MAUTIC_USERNAME, MAUTIC_PASSWORD))
        response.raise_for_status()
        data = response.json()
        smses = data.get("smses", {})
        for sms in smses.values():
            template_name = sms.get("name")
            if template_name and template_name.strip().lower() == sms_name.strip().lower():
                return sms.get("id")
    except Exception as e:
        print(f"Error al buscar sms template '{sms_name}': {e}")
    return None

def update_sms_template(sms_id, custom_sms):
    """
    Actualiza el campo message de un sma template existente en Mautic.
    """
    url = f"{MAUTIC_BASE_URL}/api/smses/{sms_id}/edit"
    payload = {"message": custom_sms}
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.patch(url, json=payload, auth=(MAUTIC_USERNAME, MAUTIC_PASSWORD), headers=headers)
        response.raise_for_status()
        print(f"SMS template (ID: {sms_id}) actualizado.")
        return True
    except Exception as e:
        print(f"Error al actualizar sms template (ID: {sms_id}): {e}")
        return False

def create_sms_template_in_mautic(city, custom_sms):
    """
    Crea un sms template en Mautic mediante la API. 
    Antes de crearlo, verifica si ya existe uno con el mismo nombre; en ese caso, solo actualiza su message.
    """
    sms_name = f"Boletin climatico - {city}"
    existing_id = get_sms_template_by_name(sms_name)
    if existing_id:
        print(f"El sms template para '{city}' ya existe. Se procederá a actualizar su message.")
        return update_sms_template(existing_id, custom_sms)
    else:
        url = f"{MAUTIC_BASE_URL}/api/smses/new"
        payload = {
            "name": sms_name,
            "message": custom_sms
        }
        headers = {"Content-Type": "application/json"}
        try:
            response = requests.post(url, json=payload, auth=(MAUTIC_USERNAME, MAUTIC_PASSWORD), headers=headers)
            response.raise_for_status()
            print(f"SMS template creado para {city}")
            return True
        except Exception as e:
            print(f"Error al crear el sms template para {city}: {e}")
            return False

def create_sms_templates():
    """
    Para cada ciudad extraída de los contactos:
      - Obtiene coordenadas y clima.
      - Crea o actualiza el sms template en Mautic vía API.
    """
    unique_cities = get_unique_cities()
    print("Ciudades únicas encontradas:")
    for city in unique_cities:
        print(city)
    
    for city in unique_cities:
        lat, lon = get_lat_lon_from_city(city)
        if lat and lon:
            temperature, date_now = get_weather_from_lat_lon(lat, lon)
            if temperature is not None:
                custom_sms = generate_custom_sms(city, temperature, date_now)
                if custom_sms:
                    create_sms_template_in_mautic(city, custom_sms)
                else:
                    print(f"Error generando SMS para {city}")
            else:
                print(f"No se pudo obtener el clima para {city}")
        else:
            print(f"No se pudieron obtener coordenadas para {city}")
