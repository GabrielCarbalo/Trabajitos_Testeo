"""
Base compartida por las pruebas de los módulos (Servicios y Registro):
configuración de pruebas con SQLite EN MEMORIA (no toca instance/trabajitos.db)
y una clase que crea una app + base de datos limpias para cada prueba.
"""

import os
import shutil
import tempfile
import unittest

from flask import g
from werkzeug.security import generate_password_hash

from app import create_app, db
from app.config import Config

# El hash se calcula una sola vez: generarlo por cada usuario/prueba sería lento.
HASH_PASSWORD = generate_password_hash("password123")


class ConfigPruebas(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"  # en memoria
    WTF_CSRF_ENABLED = False
    SERVER_NAME = None


class BaseApp(unittest.TestCase):
    """Crea una app y una base de datos limpias para cada prueba."""

    def setUp(self):
        self.app = create_app(ConfigPruebas)
        # Las fotos subidas van a una carpeta temporal propia de cada prueba,
        # nunca a app/static/uploads/. addCleanup la borra aunque la prueba falle.
        self.carpeta_uploads = tempfile.mkdtemp(prefix="trabajitos-uploads-")
        self.addCleanup(self._borrar_carpeta_uploads, self.carpeta_uploads)
        self.app.config["UPLOAD_FOLDER"] = self.carpeta_uploads
        self.contexto = self.app.app_context()
        self.contexto.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.contexto.pop()

    @staticmethod
    def _borrar_carpeta_uploads(carpeta):
        # Defensa extra: solo se borra una carpeta creada por mkdtemp dentro
        # del directorio temporal del sistema, nunca una carpeta del proyecto.
        temporal = os.path.realpath(tempfile.gettempdir())
        ruta = os.path.realpath(carpeta)
        if os.path.basename(ruta).startswith("trabajitos-uploads-") and os.path.dirname(ruta) == temporal:
            shutil.rmtree(ruta, ignore_errors=True)

    def cliente_anonimo(self):
        """
        Cliente de pruebas de una persona SIN sesión. Estas pruebas mantienen un
        app_context abierto y Flask lo reutiliza en cada request, así que hay
        que borrar el usuario que Flask-Login dejó en caché (g) por una petición
        anterior para simular de verdad a otra persona.
        """
        g.pop("_login_user", None)
        return self.app.test_client()
