import requests
import copy
from datetime import datetime

# Configuración de la API de Mautic
MAUTIC_BASE_URL = 'http://localhost:8080'  # URL de tu instancia
MAUTIC_USERNAME = 'mautic'
MAUTIC_PASSWORD = 'Khiara1919;'

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
    Nota: Es posible que debas ajustar la estructura del JSON según tu versión de Mautic.
    """
    original_data = get_campaign(original_campaign_id)
    if not original_data:
        print("No se pudo obtener la campaña original.")
        return None

    # Copia la configuración de la campaña
    new_campaign_data = copy.deepcopy(original_data.get("campaign", {}))

    # Quitar campos que no se deben clonar
    new_campaign_data.pop("id", None)
    new_campaign_data.pop("dateAdded", None)
    new_campaign_data.pop("dateModified", None)
    
    # Asigna un nuevo nombre incluyendo la hora actual
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    new_campaign_data["name"] = f"{base_campaign_name} - {current_time}"

    # Recorre los eventos para modificar el additional_data del webhook
    if "events" in new_campaign_data:
        for event in new_campaign_data["events"]:
            if event.get("type") == "campaign.sendwebhook":
                # Verifica que exista la estructura anidada en properties
                if "properties" in event and "properties" in event["properties"]:
                    event["properties"]["properties"]["additional_data"] = {
                        "args": {
                            "to": "{contactfield=mobile}@c.us",
                            "content": "Hola {contactfield=firstname}, el clima.."
                        }
                    }
    
    # Endpoint para crear una nueva campaña (verifica en tu Mautic la ruta correcta)
    url = f"{MAUTIC_BASE_URL}/api/campaigns/new"
    response = requests.post(url, json=new_campaign_data, auth=(MAUTIC_USERNAME, MAUTIC_PASSWORD))
    if response.status_code in [200, 201]:
        print("Campaña clonada exitosamente.")
        return response.json()
    else:
        print(f"Error al clonar la campaña: {response.text}")
        return None

# Ejemplo de uso:
if __name__ == "__main__":
    original_campaign_id = 1  # ID de la campaña que quieres clonar
    base_campaign_name = "Campaña Clonada - Envío recurrente"
    clone_campaign(original_campaign_id, base_campaign_name)
