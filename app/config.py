"""
Configuración de la aplicación.

Todos los valores sensibles o dependientes del entorno (clave secreta,
cadena de conexión a la base de datos) se leen desde variables de entorno
en lugar de estar escritos directamente en el código. Esto permite que el
mismo código funcione en desarrollo (SQLite) y, más adelante, en producción
(por ejemplo PostgreSQL) sin modificar nada, solo cambiando el archivo .env.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Carpeta raíz del proyecto (donde vive run.py)
BASE_DIR = Path(__file__).resolve().parent.parent

# Carga las variables definidas en el archivo .env, si existe.
load_dotenv(BASE_DIR / ".env")

# Valor de respaldo de SECRET_KEY. create_app() avisa en el log si se está
# usando fuera de modo debug (ver app/__init__.py).
CLAVE_DE_DESARROLLO = "clave-de-desarrollo-no-usar-en-produccion"


class Config:
    """Configuración base compartida por todos los entornos."""

    # Clave usada por Flask para firmar la sesión del usuario.
    # NUNCA debe quedar hardcodeada en un proyecto real; acá cae a un valor
    # de desarrollo solo si no se definió SECRET_KEY en el entorno.
    SECRET_KEY = os.environ.get("SECRET_KEY", CLAVE_DE_DESARROLLO)

    # SQLAlchemy arma la conexión a partir de DATABASE_URL.
    # Si no existe la variable, usamos SQLite dentro de instance/ como respaldo
    # para que el proyecto funcione "de una" en cualquier máquina de desarrollo.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'instance' / 'trabajitos.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Tope duro de Flask para el tamaño de cualquier request (no solo el
    # archivo): una foto de perfil o de portafolio no puede pesar más de
    # 5 MB (ver app/services/uploads.py), así que 8 MB deja margen para el
    # resto del formulario multipart sin permitir subidas absurdamente
    # grandes que ni siquiera lleguen a la validación de la aplicación.
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024
