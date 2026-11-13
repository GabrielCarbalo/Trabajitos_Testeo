"""
Pruebas de la página "Mi cuenta" (app/routes/cuenta.py).

Se ejecutan con:   python -m unittest tests.test_cuenta -v
Usan una base de datos SQLite EN MEMORIA (ver tests/base.py).
"""

import unittest

from app import db
from app.models import CuentaInvalida, User
from tests.base import HASH_PASSWORD, BaseApp


class BaseCuenta(BaseApp):
    def setUp(self):
        super().setUp()
        self.cliente = User(nombre="Cora Cliente", correo="cora@prueba.test", tipo_usuario="cliente", password_hash=HASH_PASSWORD)
        self.colab = User(nombre="Beto Colab", correo="beto@prueba.test", tipo_usuario="colaborador", password_hash=HASH_PASSWORD)
        self.admin = User(
            nombre="Adela Admin", correo="adela@prueba.test", tipo_usuario="cliente", password_hash=HASH_PASSWORD, es_admin=True
        )
        db.session.add_all([self.cliente, self.colab, self.admin])
        db.session.commit()

    def entrar_como(self, correo, password="password123"):
        cliente = self.cliente_anonimo()
        respuesta = cliente.post("/login", data={"correo": correo, "password": password})
        self.assertEqual(respuesta.status_code, 302)
        return cliente


class PruebasModelo(BaseCuenta):
    def test_rol_legible(self):
        self.assertEqual(self.cliente.rol_legible, "Cliente")
        self.assertEqual(self.colab.rol_legible, "Colaborador")
        self.assertEqual(self.admin.rol_legible, "Administrador")

    def test_nombre_invalido_lanza_cuenta_invalida_y_no_cambia(self):
        with self.assertRaises(CuentaInvalida):
            self.cliente.actualizar_nombre("   ")
        self.assertEqual(self.cliente.nombre, "Cora Cliente")

    def test_cambiar_password_junta_todos_los_errores(self):
        with self.assertRaises(CuentaInvalida) as ctx:
            self.cliente.cambiar_password("mala", "corta", "otra")
        self.assertEqual(len(ctx.exception.errores), 3)


class PruebasFlujoMVC(BaseCuenta):
    def test_anonimo_va_al_login(self):
        respuesta = self.cliente_anonimo().get("/cuenta/")
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("/login", respuesta.headers["Location"])

    def test_cada_rol_ve_sus_propios_datos(self):
        for usuario, rol in ((self.cliente, "Cliente"), (self.colab, "Colaborador"), (self.admin, "Administrador")):
            respuesta = self.entrar_como(usuario.correo).get("/cuenta/")
            self.assertEqual(respuesta.status_code, 200)
            html = respuesta.get_data(as_text=True)
            self.assertIn(usuario.correo, html)
            self.assertRegex(html, rf"<dt>Tipo de cuenta</dt>\s*<dd>{rol}</dd>")
            for otro in (self.cliente, self.colab, self.admin):
                if otro is not usuario:
                    self.assertNotIn(otro.correo, html)

    def test_no_hay_rutas_con_id_de_otra_cuenta(self):
        cliente = self.entrar_como(self.cliente.correo)
        self.assertEqual(cliente.get(f"/cuenta/{self.colab.id}").status_code, 404)

    def test_nombre_valido_se_actualiza(self):
        respuesta = self.entrar_como(self.cliente.correo).post("/cuenta/nombre", data={"nombre": "  Cora Nueva "})
        self.assertEqual(respuesta.status_code, 302)
        db.session.refresh(self.cliente)
        self.assertEqual(self.cliente.nombre, "Cora Nueva")

    def test_nombre_vacio_o_muy_largo_da_400_y_no_cambia(self):
        cliente = self.entrar_como(self.cliente.correo)
        for nombre in ("", "x" * 121):
            respuesta = cliente.post("/cuenta/nombre", data={"nombre": nombre})
            self.assertEqual(respuesta.status_code, 400)
        db.session.refresh(self.cliente)
        self.assertEqual(self.cliente.nombre, "Cora Cliente")

    def test_password_incorrecta_corta_o_distinta_da_400_y_no_cambia(self):
        cliente = self.entrar_como(self.cliente.correo)
        hash_original = self.cliente.password_hash
        casos = (
            {"password_actual": "equivocada", "password_nueva": "nueva-clave-1", "password_confirmacion": "nueva-clave-1"},
            {"password_actual": "password123", "password_nueva": "corta", "password_confirmacion": "corta"},
            {"password_actual": "password123", "password_nueva": "nueva-clave-1", "password_confirmacion": "otra-clave-1"},
        )
        for datos in casos:
            self.assertEqual(cliente.post("/cuenta/password", data=datos).status_code, 400)
        db.session.refresh(self.cliente)
        self.assertEqual(self.cliente.password_hash, hash_original)

    def test_cambio_de_password_correcto(self):
        cliente = self.entrar_como(self.cliente.correo)
        respuesta = cliente.post(
            "/cuenta/password",
            data={"password_actual": "password123", "password_nueva": "nueva-clave-1", "password_confirmacion": "nueva-clave-1"},
        )
        self.assertEqual(respuesta.status_code, 302)
        cliente.post("/logout")

        anonimo = self.cliente_anonimo()
        self.assertEqual(anonimo.post("/login", data={"correo": "cora@prueba.test", "password": "nueva-clave-1"}).status_code, 302)
        anonimo = self.cliente_anonimo()
        self.assertEqual(anonimo.post("/login", data={"correo": "cora@prueba.test", "password": "password123"}).status_code, 401)

    def test_texto_del_enlace_del_header_segun_rol(self):
        html = self.entrar_como(self.cliente.correo).get("/").get_data(as_text=True)
        encabezado = html[html.index("<header"):html.index("</header>")]
        self.assertIn("Mi perfil", encabezado)
        self.assertNotIn("Mi cuenta", encabezado)
        html = self.entrar_como(self.colab.correo).get("/").get_data(as_text=True)
        encabezado = html[html.index("<header"):html.index("</header>")]
        self.assertIn("Mi cuenta", encabezado)
        self.assertNotIn("Mi perfil", encabezado)


if __name__ == "__main__":
    unittest.main()
