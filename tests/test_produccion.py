"""
Pruebas de la preparación para producción (Railway) y de los casos de
fotografías que no cubrían los otros módulos.

Se ejecutan con:   python -m unittest tests.test_produccion -v
Igual que el resto: SQLite en memoria y carpeta de uploads temporal.
"""

import io
import os
import unittest
from unittest import mock

from flask import g

from app import create_app, db
from app.config import Config, ProductionConfig, config_del_entorno, normalizar_url_base_de_datos
from app.models import MAXIMO_FOTOS_PORTAFOLIO, PortfolioImage, User
from tests.base import HASH_PASSWORD, BaseApp
from tests.test_servicios import BaseConApp

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 32
JPG = b"\xff\xd8\xff\xe0" + b"1" * 32
WEBP = b"RIFF\x24\x00\x00\x00WEBPVP8 " + b"2" * 32


class PruebasConfiguracion(unittest.TestCase):
    """Selección de configuración y controles de arranque en producción."""

    def test_url_de_postgres_usa_el_driver_psycopg(self):
        self.assertEqual(
            normalizar_url_base_de_datos("postgresql://u:p@host:5432/db"), "postgresql+psycopg://u:p@host:5432/db"
        )
        self.assertEqual(normalizar_url_base_de_datos("postgres://u:p@h/db"), "postgresql+psycopg://u:p@h/db")
        self.assertEqual(normalizar_url_base_de_datos("sqlite:///x.db"), "sqlite:///x.db")
        self.assertEqual(
            normalizar_url_base_de_datos("postgresql+psycopg://u@h/db"), "postgresql+psycopg://u@h/db"
        )

    def test_app_env_elige_la_configuracion(self):
        with mock.patch.dict(os.environ, {"APP_ENV": "production"}):
            self.assertIs(config_del_entorno(), ProductionConfig)
        with mock.patch.dict(os.environ, {"APP_ENV": ""}):
            self.assertIs(config_del_entorno(), Config)

    def test_produccion_fuerza_debug_apagado_y_cookies_seguras(self):
        self.assertFalse(ProductionConfig.DEBUG)
        self.assertTrue(ProductionConfig.SESSION_COOKIE_SECURE)
        self.assertTrue(ProductionConfig.REMEMBER_COOKIE_SECURE)
        self.assertTrue(Config.SESSION_COOKIE_HTTPONLY)
        self.assertEqual(Config.SESSION_COOKIE_SAMESITE, "Lax")

    def test_produccion_no_arranca_sin_secret_key_database_url_ni_upload_folder(self):
        omitidas = ("SECRET_KEY", "DATABASE_URL", "UPLOAD_FOLDER")
        sin_variables = {k: v for k, v in os.environ.items() if k not in omitidas}
        with mock.patch.dict(os.environ, sin_variables, clear=True):
            with self.assertRaises(RuntimeError) as contexto:
                create_app(ProductionConfig)
        for variable in omitidas:
            self.assertIn(variable, str(contexto.exception))

    def test_produccion_rechaza_upload_folder_relativa(self):
        # Una ruta relativa terminaría dentro del contenedor, fuera del volumen.
        variables = {"SECRET_KEY": "clave-de-prueba", "DATABASE_URL": "sqlite://", "UPLOAD_FOLDER": "data/uploads"}
        with mock.patch.dict(os.environ, variables):
            with self.assertRaises(RuntimeError) as contexto:
                create_app(ProductionConfig)
        self.assertIn("UPLOAD_FOLDER", str(contexto.exception))

    def test_produccion_rechaza_secret_key_vacia(self):
        variables = {"SECRET_KEY": "  ", "DATABASE_URL": "sqlite://", "UPLOAD_FOLDER": os.path.abspath(os.sep + "data")}
        with mock.patch.dict(os.environ, variables):
            with self.assertRaises(RuntimeError) as contexto:
                create_app(ProductionConfig)
        self.assertIn("SECRET_KEY", str(contexto.exception))

    def test_produccion_rechaza_upload_folder_fuera_del_volumen(self):
        variables = {
            "SECRET_KEY": "clave-de-prueba",
            "DATABASE_URL": "sqlite://",
            "UPLOAD_FOLDER": os.path.abspath(os.sep + os.path.join("tmp", "uploads")),
            "RAILWAY_VOLUME_MOUNT_PATH": os.path.abspath(os.sep + "data"),
        }
        with mock.patch.dict(os.environ, variables):
            with self.assertRaises(RuntimeError) as contexto:
                create_app(ProductionConfig)
        self.assertIn("UPLOAD_FOLDER", str(contexto.exception))

    def test_produccion_arranca_con_las_variables_definidas(self):
        class ProduccionDePrueba(ProductionConfig):
            SQLALCHEMY_DATABASE_URI = "sqlite://"
            SECRET_KEY = "clave-de-prueba"

        variables = {
            "SECRET_KEY": "clave-de-prueba",
            "DATABASE_URL": "sqlite://",
            "UPLOAD_FOLDER": os.path.abspath(os.sep + os.path.join("data", "uploads")),
            "RAILWAY_VOLUME_MOUNT_PATH": os.path.abspath(os.sep + "data"),
        }
        with mock.patch.dict(os.environ, variables):
            app = create_app(ProduccionDePrueba)
        self.assertFalse(app.debug)


class PruebasHealthcheckYErrores(BaseApp):
    def test_health_responde_ok_sin_sesion_ni_datos_internos(self):
        respuesta = self.cliente_anonimo().get("/health")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.get_json(), {"status": "ok"})

    def test_health_da_503_si_la_base_no_responde(self):
        from sqlalchemy.exc import OperationalError

        with mock.patch.object(db.session, "execute", side_effect=OperationalError("x", {}, Exception())):
            respuesta = self.cliente_anonimo().get("/health")
        self.assertEqual(respuesta.status_code, 503)
        self.assertEqual(respuesta.get_json(), {"status": "error"})

    def test_error_500_muestra_pagina_generica_sin_traza(self):
        self.app.config["PROPAGATE_EXCEPTIONS"] = False

        @self.app.route("/_explota")
        def explota():
            raise RuntimeError("detalle interno secreto")

        respuesta = self.cliente_anonimo().get("/_explota")
        texto = respuesta.get_data(as_text=True)
        self.assertEqual(respuesta.status_code, 500)
        self.assertIn("Algo salió mal", texto)
        self.assertNotIn("detalle interno secreto", texto)
        self.assertNotIn("Traceback", texto)

    def test_caracter_nulo_da_400_y_no_500(self):
        # En PostgreSQL un \x00 en una consulta terminaba en error 500.
        cliente = self.cliente_anonimo()
        self.assertEqual(cliente.get("/explorar", query_string={"q": "a\x00b"}).status_code, 400)
        respuesta = cliente.post(
            "/registro",
            data={"nombre": "x", "correo": "a\x00b@x.com", "password": "password123", "tipo_usuario": "cliente"},
        )
        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(User.query.count(), 0)
        self.assertEqual(cliente.post("/login", data={"correo": "a\x00@x.com", "password": "x"}).status_code, 400)

    def test_pagina_gigante_en_cuentas_no_da_500(self):
        admin = User(nombre="Admin", correo="admin@prueba.test", tipo_usuario="cliente", password_hash=HASH_PASSWORD)
        admin.es_admin = True
        db.session.add(admin)
        db.session.commit()
        cliente = self.app.test_client()
        cliente.post("/login", data={"correo": "admin@prueba.test", "password": "password123"})
        for pagina in ("99999999999999999999", "-5", "abc"):
            self.assertEqual(cliente.get("/admin/cuentas", query_string={"page": pagina}).status_code, 200, pagina)


class PruebasFotografias(BaseConApp):
    """Formatos, límites, URL pública y dueño de las fotos subidas."""

    def entrar_como(self, correo):
        g.pop("_login_user", None)
        cliente = self.app.test_client()
        self.assertEqual(cliente.post("/login", data={"correo": correo, "password": "password123"}).status_code, 302)
        return cliente

    def subir_perfil(self, cliente, contenido, nombre):
        return cliente.post(
            "/dashboard/perfil",
            data={"descripcion": "Hola", "telefono_whatsapp": "", "foto": (io.BytesIO(contenido), nombre)},
            content_type="multipart/form-data",
        )

    def archivos(self, subcarpeta):
        carpeta = os.path.join(self.carpeta_uploads, subcarpeta)
        return os.listdir(carpeta) if os.path.isdir(carpeta) else []

    def test_jpg_png_y_webp_se_aceptan_y_se_sirven_desde_upload_folder(self):
        cliente = self.entrar_como("ana@prueba.test")
        for contenido, extension in ((JPG, "jpg"), (PNG, "png"), (WEBP, "webp")):
            self.assertEqual(self.subir_perfil(cliente, contenido, f"foto.{extension}").status_code, 302)
            db.session.expire_all()
            nombre = self.ana.foto_filename
            self.assertTrue(nombre.endswith("." + extension))
            # El reemplazo borra la anterior: siempre queda un solo archivo.
            self.assertEqual(self.archivos("profile"), [nombre])

            # La URL pública apunta a la ruta /uploads/ y devuelve el archivo
            # aunque UPLOAD_FOLDER esté fuera de app/static (como el volumen).
            with self.app.test_request_context():
                from app.services.image_storage import storage

                url = storage.url(nombre, "profile")
            self.assertEqual(url, f"/uploads/profile/{nombre}")
            respuesta = cliente.get(url)
            self.assertEqual(respuesta.status_code, 200)
            self.assertEqual(respuesta.data, contenido)
            self.assertEqual(respuesta.headers["X-Content-Type-Options"], "nosniff")
            respuesta.close()

    def test_tipo_falso_vacio_y_demasiado_grande_se_rechazan_sin_guardar(self):
        cliente = self.entrar_como("ana@prueba.test")
        casos = (
            (b"esto es texto, no una imagen", "foto.jpg"),
            (b"", "vacia.png"),
            (PNG + b"0" * (5 * 1024 * 1024), "grande.png"),
        )
        for contenido, nombre in casos:
            self.assertEqual(self.subir_perfil(cliente, contenido, nombre).status_code, 400, nombre)
        self.assertEqual(self.archivos("profile"), [])
        db.session.expire_all()
        self.assertIsNone(self.ana.foto_filename)

    def test_nombre_original_no_controla_la_ruta(self):
        cliente = self.entrar_como("ana@prueba.test")
        self.assertEqual(self.subir_perfil(cliente, PNG, "../../evil.php").status_code, 302)
        db.session.expire_all()
        self.assertRegex(self.ana.foto_filename, r"^[0-9a-f]{32}\.png$")

    def test_ruta_de_uploads_rechaza_subcarpetas_desconocidas_y_path_traversal(self):
        cliente = self.cliente_anonimo()
        self.assertEqual(cliente.get("/uploads/otra/archivo.png").status_code, 404)
        self.assertEqual(cliente.get("/uploads/profile/..%2F..%2Frun.py").status_code, 404)
        self.assertEqual(cliente.get("/uploads/profile/no-existe.png").status_code, 404)

    def test_archivo_de_foto_no_aprobada_solo_lo_ven_dueno_y_admin(self):
        cliente_ana = self.entrar_como("ana@prueba.test")
        cliente_ana.post(
            "/dashboard/portafolio/nueva",
            data={"foto": (io.BytesIO(PNG + b"unica"), "f.png")},
            content_type="multipart/form-data",
        )
        db.session.expire_all()
        foto = self.ana.portafolio.filter(PortfolioImage.filename.like("%.png")).order_by(PortfolioImage.id.desc()).first()
        url = f"/uploads/portfolio/{foto.filename}"
        admin = User(nombre="Admin", correo="admin@prueba.test", tipo_usuario="cliente", password_hash=HASH_PASSWORD)
        admin.es_admin = True
        db.session.add(admin)
        db.session.commit()

        self.assertEqual(self.cliente_anonimo().get(url).status_code, 200)  # aprobada: pública

        foto.rechazar("No corresponde")
        db.session.commit()
        self.assertEqual(self.cliente_anonimo().get(url).status_code, 404)
        self.assertEqual(self.entrar_como("carla@prueba.test").get(url).status_code, 404)
        self.assertEqual(self.entrar_como("ana@prueba.test").get(url).status_code, 200)
        self.assertEqual(self.entrar_como("admin@prueba.test").get(url).status_code, 200)

        # Aprobada pero de una cuenta suspendida: deja de ser pública.
        foto.aprobar()
        self.ana.usuario.banear()
        db.session.commit()
        self.assertEqual(self.cliente_anonimo().get(url).status_code, 404)

    def test_archivo_sin_registro_en_la_base_no_se_sirve(self):
        carpeta = os.path.join(self.carpeta_uploads, "portfolio")
        os.makedirs(carpeta, exist_ok=True)
        with open(os.path.join(carpeta, "huerfano.png"), "wb") as archivo:
            archivo.write(PNG)
        self.assertEqual(self.cliente_anonimo().get("/uploads/portfolio/huerfano.png").status_code, 404)

    def test_portafolio_respeta_el_maximo(self):
        cliente = self.entrar_como("beto@prueba.test")
        for i in range(MAXIMO_FOTOS_PORTAFOLIO + 1):
            cliente.post(
                "/dashboard/portafolio/nueva",
                data={"foto": (io.BytesIO(PNG + bytes([i])), "f.png")},
                content_type="multipart/form-data",
            )
        db.session.expire_all()
        self.assertEqual(self.beto.portafolio.count(), MAXIMO_FOTOS_PORTAFOLIO)
        self.assertEqual(len(self.archivos("portfolio")), MAXIMO_FOTOS_PORTAFOLIO)

    def test_no_se_puede_eliminar_ni_editar_una_foto_ajena(self):
        foto_de_ana = self.ana.portafolio.first()
        cliente = self.entrar_como("carla@prueba.test")
        self.assertEqual(cliente.post(f"/dashboard/portafolio/{foto_de_ana.id}/eliminar").status_code, 403)
        self.assertEqual(
            cliente.post(f"/dashboard/portafolio/{foto_de_ana.id}/descripcion", data={"descripcion": "x"}).status_code,
            403,
        )
        db.session.expire_all()
        self.assertIsNotNone(db.session.get(PortfolioImage, foto_de_ana.id))
        self.assertIsNone(foto_de_ana.descripcion)


if __name__ == "__main__":
    unittest.main()
