import subprocess
import time

def run_command(command):
    """
    Ejecuta un comando usando subprocess y retorna la salida.
    En caso de error, lo muestra.
    """
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"Comando ejecutado: {' '.join(command)}")
        print(result.stdout)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error ejecutando comando: {' '.join(command)}")
        print(e.stderr)
        return None

def trigger_campaigns(max_attempts=3, delay=10):
    """
    Actualiza segmentos y campañas, y luego intenta disparar las campañas en varios intentos.
    
    max_attempts: número máximo de intentos para disparar campañas.
    delay: tiempo (en segundos) de espera entre intentos.
    """
    print("Actualizando segmentos...")
    run_command(["docker", "exec", "mautic", "php", "/var/www/html/bin/console", "mautic:segments:update"])
    
    print("Actualizando campañas...")
    run_command(["docker", "exec", "mautic", "php", "/var/www/html/bin/console", "mautic:campaigns:update"])
    
    for attempt in range(1, max_attempts + 1):
        print(f"Intento {attempt} de disparar campañas...")
        output = run_command(["docker", "exec", "mautic", "php", "/var/www/html/bin/console", "mautic:campaigns:trigger"])
        
        # Puedes incluir alguna verificación en la salida (si la API o el comando indican
        # que ya no quedan campañas pendientes, por ejemplo).
        if output and "No campaigns to trigger" in output:
            print("No hay campañas pendientes, terminando el proceso de disparo.")
            break
        
        if attempt < max_attempts:
            print(f"Esperando {delay} segundos antes del siguiente intento...")
            time.sleep(delay)
    
    print("Proceso de disparo de campañas finalizado.")
