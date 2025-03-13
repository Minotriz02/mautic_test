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

def generate_custom_html(city, temperature, date_str):
    """
    Lee la plantilla base (clima_template.html), inserta en el div.container
    un bloque HTML con la temperatura, la fecha y el nombre de la ciudad, y retorna el HTML resultante.
    """
    formatted_date = format_date(date_str) if date_str else "Sin fecha"
    
    # Bloque dinámico a insertar
    dynamic_block = f"""
    <div style="text-align: center; margin-bottom: 30px">
      <div style="font-size: 48px; color: #e67e22; font-weight: bold; margin-bottom: 5px;">
        <span>{temperature}</span>°C
      </div>
      <div style="color: #95a5a6; font-size: 14px">
        {formatted_date}<br />
        {city}
      </div>
    </div>
    """
    
    try:
        with open("clima_template.html", "r", encoding="utf-8") as f:
            template_html = f.read()
    except Exception as e:
        print("Error al leer 'clima_template.html':", e)
        return None
    
    soup = BeautifulSoup(template_html, "html.parser")
    container = soup.find("div", class_="container")
    if container:
        container.clear()
        container.append(BeautifulSoup(dynamic_block, "html.parser"))
    else:
        print("No se encontró un div con clase 'container' en la plantilla.")
        return None
    
    return str(soup)

def get_email_template_by_name(email_name):
    """
    Busca en Mautic si ya existe un email template con el nombre especificado.
    Retorna el ID del template si lo encuentra, o None en caso contrario.
    Se consulta usando el campo "name" directamente, tal como se muestra en la respuesta de la API.
    """
    url = f"{MAUTIC_BASE_URL}/api/emails?where[0][col]=name&where[0][expr]=eq&where[0][val]={email_name}"
    try:
        response = requests.get(url, auth=(MAUTIC_USERNAME, MAUTIC_PASSWORD))
        response.raise_for_status()
        data = response.json()
        emails = data.get("emails", {})
        for email in emails.values():
            template_name = email.get("name")
            if template_name and template_name.strip().lower() == email_name.strip().lower():
                return email.get("id")
    except Exception as e:
        print(f"Error al buscar email template '{email_name}': {e}")
    return None

def update_email_template(email_id, custom_html):
    """
    Actualiza el campo customHtml de un email template existente en Mautic.
    """
    url = f"{MAUTIC_BASE_URL}/api/emails/{email_id}/edit"
    payload = {"customHtml": custom_html}
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.patch(url, json=payload, auth=(MAUTIC_USERNAME, MAUTIC_PASSWORD), headers=headers)
        response.raise_for_status()
        print(f"Email template (ID: {email_id}) actualizado.")
        return True
    except Exception as e:
        print(f"Error al actualizar email template (ID: {email_id}): {e}")
        return False

def create_email_template_in_mautic(city, custom_html):
    """
    Crea un email template en Mautic mediante la API. 
    Antes de crearlo, verifica si ya existe uno con el mismo nombre; en ese caso, solo actualiza su customHtml.
    El cuerpo de la petición es:
    {
        "name": "Boletin climatico - {ciudad}",
        "subject": "Boletín Climático - {contactfield=firstname}",
        "customHtml": "{html del mail de esa ciudad}"
    }
    """
    email_name = f"Boletin climatico - {city}"
    existing_id = get_email_template_by_name(email_name)
    if existing_id:
        print(f"El email template para '{city}' ya existe. Se procederá a actualizar su customHtml.")
        return update_email_template(existing_id, custom_html)
    else:
        url = f"{MAUTIC_BASE_URL}/api/emails/new"
        payload = {
            "name": email_name,
            "subject": "Boletín Climático - {contactfield=firstname}",
            "customHtml": custom_html
        }
        headers = {"Content-Type": "application/json"}
        try:
            response = requests.post(url, json=payload, auth=(MAUTIC_USERNAME, MAUTIC_PASSWORD), headers=headers)
            response.raise_for_status()
            print(f"Email template creado para {city}")
            return True
        except Exception as e:
            print(f"Error al crear el email template para {city}: {e}")
            return False

def create_email_templates():
    """
    Para cada ciudad extraída de los contactos:
      - Obtiene coordenadas y clima.
      - Genera el HTML personalizado a partir de la plantilla base.
      - Crea o actualiza el email template en Mautic vía API.
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
                custom_html = generate_custom_html(city, temperature, date_now)
                if custom_html:
                    create_email_template_in_mautic(city, custom_html)
                else:
                    print(f"Error generando HTML para {city}")
            else:
                print(f"No se pudo obtener el clima para {city}")
        else:
            print(f"No se pudieron obtener coordenadas para {city}")
