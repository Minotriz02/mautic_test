import requests
from datetime import datetime
from config import MAUTIC_BASE_URL, MAUTIC_USERNAME, MAUTIC_PASSWORD

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

def update_companie_custom_fields(companie_id, date_now, weather):
    """
    Actualiza los campos personalizados 'date_now' y 'weather' de un companie en Mautic.
    Nota: Revisa la documentación de la API de Mautic, ya que la estructura puede variar según la versión.
    """
    try:
        dt = datetime.strptime(date_now, "%Y-%m-%dT%H:%M")
        date_only = dt.date().isoformat()  
    except Exception as e:
        print(f"Error al convertir date_now: {e}")
        date_only = date_now 

    url = f"{MAUTIC_BASE_URL}/api/companies/{companie_id}/edit"
    headers = {'Content-Type': 'application/json'}
    data = {
            "datenow": date_only,
            "weather": weather
    }
    response = requests.patch(url, json=data, auth=(MAUTIC_USERNAME, MAUTIC_PASSWORD), headers=headers)
    if response.status_code == 200:
        print(f"companie {companie_id} actualizado correctamente.")
    else:
        print(f"Error al actualizar el companie {companie_id}: {response.text}")

def update_companie_weather(companie):
    """
    Para un companie dado, obtiene la ciudad, consulta la API de Open-Meteo y actualiza los campos personalizados.
    """
    companie_id = companie.get("id")
    fields = companie.get("fields", {}).get("core", {})
    
    city = fields.get("companyaddress1", {}).get("value")

    weather = None
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
                weather = current_data.get("temperature_2m")
            else:
                print(f"Error al obtener datos del clima para la ciudad {city}: {weather_response.text}")
        else:
            print(f"No se pudieron obtener coordenadas para la ciudad {city}")
    else:
        print(f"No se encontró ciudad en el companie {companie_id}")

    if date_now and weather is not None:
        update_companie_custom_fields(companie_id, date_now, weather)
    else:
        print(f"Datos incompletos del clima para el companie {companie_id}")

def process_companies_weather(companies):
    for companie in companies:
        update_companie_weather(companie)

def get_companies():
    """
    Obtiene las estaciones
    """
    url = f"{MAUTIC_BASE_URL}/api/companies"
    response = requests.get(url, auth=(MAUTIC_USERNAME, MAUTIC_PASSWORD))
    companies = []
    if response.status_code == 200:
        data = response.json()
        companies = list(data.get("companies", {}).values())
    else:
        print(f"Error al obtener companies: {response.text}")
    return companies

# Ejemplo de uso:
if __name__ == "__main__":
    companies = get_companies()
    if companies:
        process_companies_weather(companies)
    else:
        print("No se encontraron companies para actualizar.")
