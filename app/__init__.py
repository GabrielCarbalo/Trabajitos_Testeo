"""
Application factory de TRABAJITOS.

Usamos el patrón "create_app()" (en vez de crear la app directamente a nivel
de módulo) porque permite:
  - inicializar las extensiones (SQLAlchemy, Flask-Login) sin importarlas
    en un orden problemático (imports circulares con los modelos);
  - crear varias instancias de la app con configuraciones distintas
    (por ejemplo una para tests, otra para desarrollo).
"""

import os
from datetime import datetime, timezone

from flask import Flask, flash, render_template
from flask_login import LoginManager, current_user, logout_user
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from werkzeug.routing import IntegerConverter

from app.config import CLAVE_DE_DESARROLLO, Config


class IdConverter(IntegerConverter):
    """
    Igual que el <int:...> de Flask, pero con un tope: el id más grande que
    entra en un INTEGER de SQLite/PostgreSQL (64 bits). Sin esto, una URL
    como /colaborador/99999999999999999999 llega hasta la consulta y rompe
    con un error 500 (OverflowError) en vez de responder 404.
    """

    def __init__(self, url_map, *args, **kwargs):
        kwargs.setdefault("max", 2**63 - 1)
        super().__init__(url_map, *args, **kwargs)

# Las extensiones se crean acá "vacías" y se conectan a la app en create_app().
db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Iniciá sesión para continuar."
login_manager.login_message_category = "info"


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    if app.config["SECRET_KEY"] == CLAVE_DE_DESARROLLO and not (app.debug or app.testing):
        app.logger.warning(
            "SECRET_KEY no está definida: se está usando la clave de desarrollo. "
            "Definí una propia en .env antes de publicar la aplicación."
        )

    # La base SQLite por defecto vive en instance/, pero SQLite no crea
    # carpetas: si no existe, "flask db upgrade" falla con "unable to open
    # database file" en una instalación nueva.
    os.makedirs(app.instance_path, exist_ok=True)

    # Tiene que registrarse ANTES que los blueprints: cada ruta toma su
    # converter en el momento en que se agrega al mapa de URLs.
    app.url_map.converters["int"] = IdConverter

    db.init_app(app)
    login_manager.init_app(app)
    # Protección CSRF: todo formulario que hace POST necesita incluir
    # {{ csrf_token() }} en un campo oculto (ver templates de auth/). Sin
    # esto, cualquier sitio externo podría enviar formularios en nombre de
    # un usuario con sesión iniciada.
    csrf.init_app(app)

    # Los modelos se importan acá (y no arriba del archivo) para evitar
    # imports circulares: models.py necesita "db", que se termina de
    # inicializar recién en la línea anterior.
    from app import models  # noqa: F401

    # Flask-Migrate necesita los modelos ya importados para poder detectar
    # cambios de esquema (flask db migrate) sin perder los datos existentes.
    migrate.init_app(app, db)

    # Registro de blueprints: cada archivo de app/routes/ agrupa las rutas
    # de una parte de la aplicación (público, autenticación, panel privado).
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)

    @app.before_request
    def cerrar_sesion_de_cuentas_baneadas():
        """
        El login ya bloquea a las cuentas baneadas (ver app/routes/auth.py),
        pero alguien que tenía la sesión abierta desde ANTES del baneo seguía
        navegando como si nada en las páginas públicas. Esto corta esa
        sesión en cualquier página, no solo en el panel.
        """
        if current_user.is_authenticated and current_user.esta_baneado:
            logout_user()
            flash("Esta cuenta fue suspendida por incumplir las normas de la plataforma.", "error")

    @app.context_processor
    def inyectar_anio_actual():
        """Disponibiliza el año actual en todos los templates (usado en el footer)."""
        return {"anio_actual": datetime.now(timezone.utc).year}

    @app.context_processor
    def inyectar_helpers_imagenes():
        """
        Funciones para armar URLs de imágenes subidas, disponibles en
        cualquier template sin tener que pasarlas manualmente desde cada
        ruta. avatar_url() devuelve None si el colaborador no tiene foto o
        si todavía no está aprobada — los templates deciden qué mostrar en
        ese caso (la inicial del nombre, ver partials/avatar.html).
        """
        from app.services.image_storage import storage
        from app.services.uploads import SUBCARPETA_PERFIL, SUBCARPETA_PORTAFOLIO

        def avatar_url(perfil):
            if perfil is not None and perfil.foto_visible:
                return storage.url(perfil.foto_filename, SUBCARPETA_PERFIL)
            return None

        def portafolio_url(foto):
            return storage.url(foto.filename, SUBCARPETA_PORTAFOLIO)

        return {"avatar_url": avatar_url, "portafolio_url": portafolio_url}

    @app.context_processor
    def inyectar_etiqueta_moderacion():
        """Texto y clase CSS legibles para un moderation_status ('pending'/'approved'/'flagged'/'rejected')."""
        etiquetas = {
            "pending": ("Pendiente de revisión", "pendiente"),
            "approved": ("Aprobada", "aprobada"),
            "flagged": ("En revisión", "revision"),
            "rejected": ("Rechazada", "rechazada"),
        }

        def etiqueta_moderacion(estado):
            return etiquetas.get(estado, (estado, "pendiente"))

        return {"etiqueta_moderacion": etiqueta_moderacion}

    @app.errorhandler(403)
    def prohibido(_error):
        return render_template(
            "error.html",
            codigo=403,
            titulo="No tenés acceso a esta página",
            mensaje="Esta sección es solo para cuentas de colaborador.",
        ), 403

    @app.errorhandler(404)
    def no_encontrado(_error):
        return render_template(
            "error.html",
            codigo=404,
            titulo="Esta página no existe",
            mensaje="Revisá la dirección o volvé al inicio.",
        ), 404

    @app.errorhandler(413)
    def archivo_demasiado_grande(_error):
        return render_template(
            "error.html",
            codigo=413,
            titulo="El archivo es demasiado grande",
            mensaje="Elegí una imagen de hasta 5 MB e intentá de nuevo.",
        ), 413

    return app
