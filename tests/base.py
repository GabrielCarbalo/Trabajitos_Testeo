"""
Base compartida por las pruebas de los módulos (Servicios y Registro):
configuración de pruebas con SQLite EN MEMORIA (no toca instance/trabajitos.db)
y una clase que crea una app + base de datos limpias para cada prueba.
"""

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
        self.contexto = self.app.app_context()
        self.contexto.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.contexto.pop()

    def cliente_anonimo(self):
        """
        Cliente de pruebas de una persona SIN sesión. Estas pruebas mantienen un
        app_context abierto y Flask lo reutiliza en cada request, así que hay
        que borrar el usuario que Flask-Login dejó en caché (g) por una petición
        anterior para simular de verdad a otra persona.
        """
        g.pop("_login_user", None)
        return self.app.test_client()
