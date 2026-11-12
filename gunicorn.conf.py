"""
Configuración de Gunicorn (servidor de producción). Gunicorn lee este
archivo automáticamente si se ejecuta desde la raíz del proyecto:

    gunicorn run:app

El puerto se toma de la variable PORT que inyecta Railway, leída acá en
Python para no depender de que el comando de inicio pase por una shell.
"""

import os

bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
# WEB_CONCURRENCY permite ajustar la cantidad de procesos sin tocar código.
workers = int(os.environ.get("WEB_CONCURRENCY", "2"))
timeout = 60
# Logs de acceso y errores a la salida estándar (los muestra Railway).
accesslog = "-"
errorlog = "-"
