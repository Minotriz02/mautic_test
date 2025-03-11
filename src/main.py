# main.py
from email_sender import send_weather_emails
from sms_sender import send_sms_notifications
from campaign_module import clone_campaign, trigger_campaigns
from config import CAMPAIGN_ORIGINAL_ID, BASE_CAMPAIGN_NAME

def send_clima_bulletin():
    print("Iniciando el envío del boletín de clima...")
    
    print("\nEnviando boletín por Email:")
    send_weather_emails()
    
    # print("\nEnviando boletín por SMS:")
    # send_sms_notifications()
    
    # print("\nCreando campaña de boletin de clima:")
    # clone_campaign(CAMPAIGN_ORIGINAL_ID, BASE_CAMPAIGN_NAME)
    
    # print("\nEjecutando comandos de campaña en Mautic:")
    # trigger_campaigns()

if __name__ == "__main__":
    send_clima_bulletin()
