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
# usando fuera de modo debug, y en producción directamente no arranca
# (ver app/__init__.py).
CLAVE_DE_DESARROLLO = "clave-de-desarrollo-no-usar-en-produccion"


def normalizar_url_base_de_datos(url):
    """
    Railway (y otros servicios) entregan la conexión como "postgresql://..."
    o con el alias viejo "postgres://...". SQLAlchemy interpreta ese esquema
    como el driver psycopg2, pero el proyecto usa psycopg 3 (ver
    requirements.txt), así que se indica el driver de forma explícita.
    Cualquier otra URL (por ejemplo la SQLite de desarrollo) queda igual.
    """
    if not url:
        return url
    for prefijo in ("postgres://", "postgresql://"):
        if url.startswith(prefijo):
            return "postgresql+psycopg://" + url[len(prefijo):]
    return url


class Config:
    """Configuración base compartida por todos los entornos."""

    # Clave usada por Flask para firmar la sesión del usuario.
    # NUNCA debe quedar hardcodeada en un proyecto real; acá cae a un valor
    # de desarrollo solo si no se definió SECRET_KEY en el entorno.
    SECRET_KEY = os.environ.get("SECRET_KEY", CLAVE_DE_DESARROLLO)

    # SQLAlchemy arma la conexión a partir de DATABASE_URL.
    # Si no existe la variable, usamos SQLite dentro de instance/ como respaldo
    # para que el proyecto funcione "de una" en cualquier máquina de desarrollo.
    SQLALCHEMY_DATABASE_URI = normalizar_url_base_de_datos(
        os.environ.get("DATABASE_URL", f"sqlite:///{BASE_DIR / 'instance' / 'trabajitos.db'}")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Descarta conexiones que PostgreSQL cerró mientras estaban inactivas
    # en el pool, en vez de fallar en la siguiente consulta. En SQLite no
    # cambia nada.
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # Carpeta donde se guardan las fotos subidas (perfil y portafolio). Vacía
    # = app/static/uploads/ (desarrollo). En producción apunta al volumen
    # persistente, por ejemplo /data/uploads (ver DEPLOY_RAILWAY.md).
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER") or None

    # Cookies de sesión: nunca accesibles desde JavaScript (HttpOnly, ya es
    # el valor por defecto de Flask) y no enviadas en peticiones POST desde
    # otros sitios (SameSite=Lax). "Secure" se activa solo en producción
    # (HTTPS): en http://localhost el navegador las descartaría.
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"

    # Tope duro de Flask para el tamaño de cualquier request (no solo el
    # archivo): una foto de perfil o de portafolio no puede pesar más de
    # 5 MB (ver app/services/uploads.py), así que 8 MB deja margen para el
    # resto del formulario multipart sin permitir subidas absurdamente
    # grandes que ni siquiera lleguen a la validación de la aplicación.
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024


class ProductionConfig(Config):
    """
    Producción (Railway). Se activa con APP_ENV=production. create_app()
    exige además SECRET_KEY y DATABASE_URL propias: sin DATABASE_URL la app
    usaría una SQLite dentro del contenedor, que se pierde en cada deploy.
    """

    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


def config_del_entorno():
    """Clase de configuración según APP_ENV (por defecto, desarrollo)."""
    if os.environ.get("APP_ENV", "").strip().lower() == "production":
        return ProductionConfig
    return Config
