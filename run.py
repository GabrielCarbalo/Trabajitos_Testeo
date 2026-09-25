"""
Punto de entrada para ejecutar TRABAJITOS en desarrollo.

Uso:
    python run.py

Esto levanta un servidor local (por defecto en http://127.0.0.1:5000)
con recarga automática al guardar cambios en el código.
"""

import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    # FLASK_DEBUG se lee desde .env (ver .env.example). Por defecto queda
    # activado para no romper el flujo de desarrollo si todavía no se creó
    # el archivo .env, pero en producción debe definirse en "0".
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(debug=debug)
