import json
import requests
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

def get_weather_from_lat_lon(lat, lon):
    """
    Obtiene la temperatura actual desde la API de Open-Meteo utilizando latitud y longitud.
    """
    # Usamos el parámetro current_weather=true para obtener el clima actual.
    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    weather_response = requests.get(weather_url)
    if weather_response.status_code == 200:
        weather_data = weather_response.json()
        current_data = weather_data.get("current_weather", {})
        # En Open-Meteo, la temperatura actual viene en el campo "temperature"
        temperature = current_data.get("temperature")
        date_now = current_data.get("time")
        return temperature, date_now
    return None, None

def company_exists(company_name):
    """
    Consulta en Mautic si ya existe una compañía con el nombre (ciudad) especificado.
    Se realiza una búsqueda a través de la API de companies.
    """
    url = f"{MAUTIC_BASE_URL}/api/companies?where[0][col]=companyname&where[0][expr]=eq&where[0][val]={company_name}"
    try:
        response = requests.get(url, auth=(MAUTIC_USERNAME, MAUTIC_PASSWORD))
        response.raise_for_status()
        data = response.json()
        companies = data.get("companies", {})
        # Se itera sobre las companies para encontrar una que tenga el mismo nombre en el campo core.name
        for comp in companies.values():
            comp_name = comp.get("fields", {}).get("core", {}).get("name", {}).get("value")
            if comp_name and comp_name.strip().lower() == company_name.strip().lower():
                return True
    except requests.RequestException as e:
        print(f"Error al buscar company '{company_name}': {e}")
    return False

def create_company(company_name, weather):
    """
    Crea una nueva compañía en Mautic con el nombre de la ciudad y el atributo "weather".
    Se asume que en Mautic existe un campo (posiblemente custom) llamado "weather".
    """
    url = f"{MAUTIC_BASE_URL}/api/companies/new"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "companyname": company_name,
        "weather": weather  # Este campo debe existir o estar mapeado en Mautic
    }
    try:
        response = requests.post(url, json=payload, auth=(MAUTIC_USERNAME, MAUTIC_PASSWORD), headers=headers)
        response.raise_for_status()
        company_info = response.json().get("company", {})
        company_id = company_info.get("id")
        print(f"Company creada: {company_name} (ID: {company_id}) con weather: {weather}")
        return company_id
    except requests.RequestException as e:
        print(f"Error al crear company '{company_name}': {e}")
        return None

def etl_import_cities():
    """
    Lee el archivo JSON de usuarios, extrae las ciudades (companies) únicas y para cada una:
      - Verifica si ya existe en Mautic.
      - Si no existe, obtiene coordenadas y clima actual.
      - Crea la compañía en Mautic con el atributo 'weather'.
    """
    users_file = 'users.json'
    unique_cities = set()
    with open(users_file, 'r', encoding='utf-8') as file:
        users = json.load(file)
        for user in users:
            # Se asume que el campo "cities" es un array (o puede ser string)
            cities = user.get("cities")
            if isinstance(cities, list):
                for city in cities:
                    unique_cities.add(city.strip())
            elif isinstance(cities, str):
                unique_cities.add(cities.strip())
    
    print("Ciudades únicas encontradas:")
    for city in unique_cities:
        print(city)
    
    # Procesar cada ciudad: obtener clima y crear company si no existe
    for city in unique_cities:
        if company_exists(city):
            print(f"La compañía para la ciudad '{city}' ya existe. Se omite la creación.")
        else:
            lat, lon = get_lat_lon_from_city(city)
            if lat and lon:
                weather, date_now = get_weather_from_lat_lon(lat, lon)
                if weather is not None:
                    create_company(city, weather)
                else:
                    print(f"No se pudo obtener el clima para la ciudad '{city}'.")
            else:
                print(f"No se pudieron obtener coordenadas para la ciudad '{city}'.")
