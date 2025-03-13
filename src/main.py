# main.py
from config import CAMPAIGN_ORIGINAL_ID, BASE_CAMPAIGN_NAME
from import_contacts import etl_import_contacts
from import_cities import etl_import_cities
from create_segments import process_segments


def send_clima_bulletin():
    print("Iniciando proceso...")
    
    print("\nImportando contactos:")
    etl_import_contacts()

    print("\nImportando ciudades:")
    etl_import_cities()

    print("\nCreando segmentos:")
    process_segments()

if __name__ == "__main__":
    send_clima_bulletin()
