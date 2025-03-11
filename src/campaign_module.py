# campaign_module.py
import copy
import requests
import subprocess
from datetime import datetime
from config import MAUTIC_BASE_URL, MAUTIC_USERNAME, MAUTIC_PASSWORD, CAMPAIGN_ORIGINAL_ID, BASE_CAMPAIGN_NAME

def get_campaign(campaign_id):
    """
    Obtiene la configuración de la campaña original.
    """
    url = f"{MAUTIC_BASE_URL}/api/campaigns/{campaign_id}"
    response = requests.get(url, auth=(MAUTIC_USERNAME, MAUTIC_PASSWORD))
    if response.status_code == 200:
        return response.json()  # Se espera que la respuesta tenga la configuración de la campaña
    else:
        print(f"Error al obtener la campaña {campaign_id}: {response.text}")
        return None

def clone_campaign(original_campaign_id, base_campaign_name):
    """
    Clona la campaña original con un nuevo nombre que incluye la hora actual.
    """
    original_data = get_campaign(original_campaign_id)
    if not original_data:
        print("No se pudo obtener la campaña original.")
        return None

    new_campaign_data = copy.deepcopy(original_data.get("campaign", {}))
    new_campaign_data.pop("id", None)
    new_campaign_data.pop("dateAdded", None)
    new_campaign_data.pop("dateModified", None)
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    new_campaign_data["name"] = f"{base_campaign_name} - {current_time}"
    
    url = f"{MAUTIC_BASE_URL}/api/campaigns/new"
    response = requests.post(url, json=new_campaign_data, auth=(MAUTIC_USERNAME, MAUTIC_PASSWORD))
    if response.status_code in [200, 201]:
        print("Campaña clonada exitosamente.")
        return response.json()
    else:
        print(f"Error al clonar la campaña: {response.text}")
        return None

def trigger_campaigns():
    """
    Ejecuta los comandos CLI de Mautic para actualizar segmentos, campañas y disparar las campañas.
    """
    try:
        print("Actualizando segmentos...")
        subprocess.run(["docker", "exec", "mautic", "php", "/var/www/html/bin/console", "mautic:segments:update"], check=True)
        print("Actualizando campañas...")
        subprocess.run(["docker", "exec", "mautic", "php", "/var/www/html/bin/console", "mautic:campaigns:update"], check=True)
        print("Disparando campañas...")
        subprocess.run(["docker", "exec", "mautic", "php", "/var/www/html/bin/console", "mautic:campaigns:trigger"], check=True)
        print("Campañas disparadas con éxito.")
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar comando: {e}")
