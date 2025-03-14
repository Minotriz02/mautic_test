import requests
from config import MAUTIC_BASE_URL, MAUTIC_USERNAME, MAUTIC_PASSWORD

def get_segments():
    """
    Retorna todas las listas/segmentos disponibles en Mautic.
    """
    url = f"{MAUTIC_BASE_URL}/api/segments"
    try:
        response = requests.get(url, auth=(MAUTIC_USERNAME, MAUTIC_PASSWORD))
        response.raise_for_status()
        data = response.json()
        lists_data = data.get("lists", {})
        # Dependiendo de la versión de Mautic, "lists_data" puede ser dict o list.
        # Normalizamos a una lista de segmentos.
        if isinstance(lists_data, dict):
            return lists_data.values()
        return lists_data
    except requests.RequestException as e:
        print(f"Error al obtener segmentos: {e}")
        return []

def get_segment_id_by_name(segment_name):
    """
    Retorna el ID del segmento con nombre 'segment_name', o None si no existe.
    """
    segments = get_segments()
    for seg in segments:
        if seg.get("name") == segment_name:
            return seg.get("id")
    return None

def get_email_template_by_name(email_name):
    """
    Busca un email template por nombre y retorna su ID, o None si no existe.
    """
    url = f"{MAUTIC_BASE_URL}/api/emails?where[0][col]=name&where[0][expr]=eq&where[0][val]={email_name}"
    try:
        response = requests.get(url, auth=(MAUTIC_USERNAME, MAUTIC_PASSWORD))
        response.raise_for_status()
        data = response.json()
        emails = data.get("emails", {})
        for email in emails.values():
            if email.get("name", "").strip().lower() == email_name.strip().lower():
                return email.get("id")
    except requests.RequestException as e:
        print(f"Error al buscar email template '{email_name}': {e}")
    return None

def get_sms_by_name(sms_name):
    """
    Busca un SMS por nombre y retorna su ID, o None si no existe.
    """
    url = f"{MAUTIC_BASE_URL}/api/smses?where[0][col]=name&where[0][expr]=eq&where[0][val]={sms_name}"
    try:
        response = requests.get(url, auth=(MAUTIC_USERNAME, MAUTIC_PASSWORD))
        response.raise_for_status()
        data = response.json()
        messages = data.get("smses", {})
        for sms in messages.values():
            if sms.get("name", "").strip().lower() == sms_name.strip().lower():
                return sms.get("id")
    except requests.RequestException as e:
        print(f"Error al buscar SMS '{sms_name}': {e}")
    return None

def create_campaign_for_city(city):
    """
    Crea una campaña en Mautic que apunte al segmento 'Boletin clima - {city}' y
    tenga 3 acciones: enviar email, enviar SMS y enviar webhook.
    """
    segment_name = f"Boletin clima - {city}"
    segment_id = get_segment_id_by_name(segment_name)
    if not segment_id:
        print(f"No se encontró el segmento '{segment_name}'. No se creará campaña para {city}.")
        return
    
    # Obtener el ID del email y del SMS
    email_name = f"Boletin climatico - {city}"
    email_id = get_email_template_by_name(email_name)
    if not email_id:
        print(f"No se encontró el email '{email_name}'. No se creará campaña para {city}.")
        return
    
    sms_name = f"Boletin climatico - {city}"
    sms_id = get_sms_by_name(sms_name)
    if not sms_id:
        print(f"No se encontró el SMS '{sms_name}'. No se creará campaña para {city}.")
        return
    
    # Estructura del payload para crear la campaña
    campaign_payload = {
        "name": f"Campaña - {city}",
        "description": f"Campaña para {city}",
        "isPublished": True,
        "publishUp": None,
        "publishDown": None,
        # Asignamos el segmento
        "lists": [{
            "id": segment_id
        }],
        # Definimos los 3 eventos (acciones)
        "events": [
            {
                "id": "new1",
                "name": f"Enviar Email - {city}",
                "type": "email.send",
                "eventType": "action",
                "order": 1,
                "properties": {
                    "canvasSettings": {
                        "droppedX": "520",
                        "droppedY": "155"
                    },
                    "email": email_id
                },
                "triggerDate": None,
                "triggerInterval": 1,
                "triggerIntervalUnit": "d",
                "triggerHour": None,
                "triggerRestrictedStartHour": None,
                "triggerRestrictedStopHour": None,
                "triggerRestrictedDaysOfWeek": [],
                "triggerMode": "immediate",
                "decisionPath": None,
                "parent": None
            },
            {
                "id": "new2",
                "name": f"Enviar SMS - {city}",
                "type": "sms.send_text_sms",
                "eventType": "action",
                "order": 2,
                "properties": {
                    "canvasSettings": {
                        "droppedX": "710",
                        "droppedY": "291"
                    },
                    "sms": sms_id
                },
                "triggerDate": None,
                "triggerInterval": 1,
                "triggerIntervalUnit": "d",
                "triggerHour": None,
                "triggerRestrictedStartHour": None,
                "triggerRestrictedStopHour": None,
                "triggerRestrictedDaysOfWeek": [],
                "triggerMode": "immediate",
                "decisionPath": "yes",
                "parent": {
                    "id": "new1"
                }
            },
            {
                "id": "new3",
                "name": "Enviar texto simple",
                "type": "campaign.sendwebhook",
                "eventType": "action",
                "order": 3,
                "properties": {
                    "canvasSettings": {
                        "droppedX": "910",
                        "droppedY": "401"
                    },
                    "url": "http://waha:3000/api/sendText",
                    "method": "post",
                    "additional_data": {
                        "list": [
                            {
                                "label": "chatId",
                                "value": "{contactfield=mobilewithoutplus}@c.us"
                            },
                            {
                                "label": "reply_to",
                                "value": "null"
                            },
                            {
                                "label": "text",
                                "value": "Hola {contactfield=firstname}, el clima.."
                            },
                            {
                                "label": "linkPreview",
                                "value": "true"
                            },
                            {
                                "label": "session",
                                "value": "default"
                            }
                        ]
                    },
                    "headers": {
                        "list": [
                            {
                                "label": "content-type",
                                "value": "application/json"
                            }
                        ]
                    }
                },
                "triggerDate": None,
                "triggerInterval": 1,
                "triggerIntervalUnit": "d",
                "triggerHour": None,
                "triggerRestrictedStartHour": None,
                "triggerRestrictedStopHour": None,
                "triggerRestrictedDaysOfWeek": [],
                "triggerMode": "immediate",
                "decisionPath": "yes",
                "parent": {
                    "id": "new2"
                }
            }
        ],
        "canvasSettings": {
            "nodes": [
                {
                    "id": "new1",
                    "positionX": "810",
                    "positionY": "186"
                },
                {
                    "id": "new2",
                    "positionX": "710",
                    "positionY": "291"
                },
                {
                    "id": "new3",
                    "positionX": "910",
                    "positionY": "401"
                },
                {
                    "id": "lists",
                    "positionX": "833",
                    "positionY": "50"
                }
            ],
            "connections": [
                {
                    "sourceId": "lists",
                    "targetId": "new1",
                    "anchors": {
                        "source": "leadsource",
                        "target": "top"
                    }
                },
                {
                    "sourceId": "new1",
                    "targetId": "new2",
                    "anchors": {
                        "source": "bottom",
                        "target": "top"
                    }
                },
                {
                    "sourceId": "new2",
                    "targetId": "new3",
                    "anchors": {
                        "source": "bottom",
                        "target": "top"
                    }
                }
            ]
        }
    }
    
    # Enviamos la petición para crear la campaña
    url = f"{MAUTIC_BASE_URL}/api/campaigns/new"
    try:
        response = requests.post(url, json=campaign_payload,
                                auth=(MAUTIC_USERNAME, MAUTIC_PASSWORD))
        response.raise_for_status()
        data = response.json()
        campaign_id = data.get("campaign", {}).get("id")
        print(f"Campaña para '{city}' creada con ID: {campaign_id}")
    except requests.RequestException as e:
        print(f"Error al crear la campaña para '{city}': {e}")

def create_campaigns():
    """
    Busca todos los segmentos que tengan el prefijo 'Boletin clima - ' y para cada uno
    obtiene el nombre de la ciudad y crea la campaña correspondiente.
    """
    segments = get_segments()
    for seg in segments:
        seg_name = seg.get("name", "")
        # Verificamos si el segmento sigue la convención "Boletin clima - X"
        prefix = "Boletin clima - "
        if seg_name.startswith(prefix):
            city = seg_name.replace(prefix, "").strip()
            create_campaign_for_city(city)
