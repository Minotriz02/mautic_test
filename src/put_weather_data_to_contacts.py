import requests
from datetime import datetime
from config import MAUTIC_BASE_URL, MAUTIC_USERNAME, MAUTIC_PASSWORD
from email_sender import get_contacts_with_climabulletin

def get_lat_lon_from_city(city):
    """
    Utiliza la API de Nominatim para convertir el nombre de la ciudad en latitud y longitud.
    """
    url = "https://nominatim.openstreetmap.org/search.php"
    params = {
        "q": city,
        "format": "json"
    }
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    if data:
        return data[0]["lat"], data[0]["lon"]
    else:
        return None, None

def update_contact_custom_fields(contact_id, date_now, temperature_1, temperature2=None):
    """
    Actualiza los campos personalizados 'date_now' y 'temperature_1' de un contacto en Mautic.
    Nota: Revisa la documentación de la API de Mautic, ya que la estructura puede variar según la versión.
    """
    try:
        dt = datetime.strptime(date_now, "%Y-%m-%dT%H:%M")
        date_only = dt.date().isoformat()  
    except Exception as e:
        print(f"Error al convertir date_now: {e}")
        date_only = date_now 

    url = f"{MAUTIC_BASE_URL}/api/contacts/{contact_id}/edit"
    headers = {'Content-Type': 'application/json'}
    data = {
            "datenow": date_only,
            "temperature1": temperature_1
    }
    if temperature2 is not None:
        data["temperature2"] = temperature2
    response = requests.patch(url, json=data, auth=(MAUTIC_USERNAME, MAUTIC_PASSWORD), headers=headers)
    if response.status_code == 200:
        print(f"Contacto {contact_id} actualizado correctamente.")
    else:
        print(f"Error al actualizar el contacto {contact_id}: {response.text}")

def update_contact_weather(contact):
    """
    Para un contacto dado, obtiene la ciudad, consulta la API de Open-Meteo y actualiza los campos personalizados.
    """
    contact_id = contact.get("id")
    fields = contact.get("fields", {}).get("core", {})
    
    # Extraemos la primera ciudad y la segunda (si existe)
    city = fields.get("city", {}).get("value")
    city2 = fields.get("city2", {}).get("value")

    temperature1 = None
    date_now = None

    if city:
        lat, lon = get_lat_lon_from_city(city)
        if lat and lon:
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m"
            weather_response = requests.get(weather_url)
            if weather_response.status_code == 200:
                weather_data = weather_response.json()
                current_data = weather_data.get("current", {})
                date_now = current_data.get("time")
                temperature1 = current_data.get("temperature_2m")
            else:
                print(f"Error al obtener datos del clima para la ciudad {city}: {weather_response.text}")
        else:
            print(f"No se pudieron obtener coordenadas para la ciudad {city}")
    else:
        print(f"No se encontró ciudad en el contacto {contact_id}")

    temperature2 = None
    if city2:
        lat2, lon2 = get_lat_lon_from_city(city2)
        if lat2 and lon2:
            weather_url2 = f"https://api.open-meteo.com/v1/forecast?latitude={lat2}&longitude={lon2}&current=temperature_2m"
            weather_response2 = requests.get(weather_url2)
            if weather_response2.status_code == 200:
                weather_data2 = weather_response2.json()
                current_data2 = weather_data2.get("current", {})
                temperature2 = current_data2.get("temperature_2m")
            else:
                print(f"Error al obtener datos del clima para la ciudad {city2}: {weather_response2.text}")
        else:
            print(f"No se pudieron obtener coordenadas para la ciudad {city2}")

    if date_now and temperature1 is not None:
        update_contact_custom_fields(contact_id, date_now, temperature1, temperature2)
    else:
        print(f"Datos incompletos del clima para el contacto {contact_id}")

def process_contacts_weather(contacts):
    for contact in contacts:
        update_contact_weather(contact)

# Ejemplo de uso:
if __name__ == "__main__":
    contacts = get_contacts_with_climabulletin()
    if contacts:
        process_contacts_weather(contacts)
    else:
        print("No se encontraron contactos para actualizar.")
