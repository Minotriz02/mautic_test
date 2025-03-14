import os
import imgkit
import requests
from config import MAUTIC_BASE_URL, MAUTIC_USERNAME, MAUTIC_PASSWORD

def get_email_templates():
    """
    Obtiene todos los email templates desde Mautic.
    Se usa el endpoint /api/emails y se retorna la lista de templates.
    """
    url = f"{MAUTIC_BASE_URL}/api/emails"
    try:
        response = requests.get(url, auth=(MAUTIC_USERNAME, MAUTIC_PASSWORD))
        response.raise_for_status()
        data = response.json()
        emails = data.get("emails", {})
        return emails.values()
    except Exception as e:
        print("Error al obtener email templates:", e)
        return []

# Es necesario tener descargado wkhtmltopdf
def generate_image_from_html(html_content, output_filename):
    """
    Convierte el contenido HTML en una imagen PNG usando imgkit.
    Asegúrate de que wkhtmltoimage esté instalado y en el PATH.
    """
    options = {
        'format': 'png',
        'encoding': "UTF-8"
    }
    try:
        imgkit.from_string(html_content, output_filename, options=options)
        print(f"Imagen guardada: {output_filename}")
    except Exception as e:
        print(f"Error al generar la imagen '{output_filename}': {e}")

def create_images_bulletin():
    emails = get_email_templates()
    output_dir = "email_images"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for email in emails:
        email_name = email.get("name")
        custom_html = email.get("customHtml")
        if email_name and custom_html:
            # Sanitizamos el nombre para usarlo como nombre de archivo
            safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in email_name)
            output_filename = os.path.join(output_dir, f"{safe_name}.png")
            generate_image_from_html(custom_html, output_filename)
        else:
            print("No se encontró nombre o HTML para un email template.")
