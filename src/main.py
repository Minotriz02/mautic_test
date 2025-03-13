# main.py
from config import CAMPAIGN_ORIGINAL_ID, BASE_CAMPAIGN_NAME
from import_contacts import etl_import_contacts
from create_segments import process_segments
from create_mails import create_email_templates
from create_sms import create_sms_templates


def send_clima_bulletin():
    print("Iniciando proceso...")
    
    print("\nImportando contactos:")
    etl_import_contacts()

    print("\nCreando segmentos:")
    process_segments()

    print("\nCreando mails:")
    create_email_templates()

    print("\nCreando text messages:")
    create_sms_templates()

if __name__ == "__main__":
    send_clima_bulletin()
