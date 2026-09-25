"""
Pruebas del módulo "Registro de usuarios" (MVC + POO).

Se ejecutan con:   python -m unittest tests.test_registro -v
Usan una base de datos SQLite EN MEMORIA (ver tests/base.py).

Dos grupos:
  - PruebasModelo: la clase User por sí sola (POO): validación, encapsulación,
    hash de contraseña, creación del perfil de colaborador.
  - PruebasFlujoMVC: Vista -> Controller -> Model -> Vista con el cliente de
    pruebas de Flask.
"""

import unittest

from app import db
from app.models import CollaboratorProfile, RegistroInvalido, User
from tests.base import BaseApp

DATOS_VALIDOS = {
    "nombre": "  Lucía Pérez ",
    "correo": "  Lucia@Prueba.TEST ",
    "password": "clave-segura-1",
    "tipo_usuario": "colaborador",
}


class PruebasModelo(BaseApp):
    """POO: la clase User protege sus propias reglas, sin pasar por ningún formulario."""

    def test_registrar_colaborador_normaliza_y_crea_perfil(self):
        usuario = User.registrar(DATOS_VALIDOS)
        self.assertEqual(usuario.nombre, "Lucía Pérez")
        self.assertEqual(usuario.correo, "lucia@prueba.test")
        self.assertTrue(usuario.es_colaborador)
        self.assertIsInstance(usuario.perfil_colaborador, CollaboratorProfile)

    def test_registrar_cliente_no_crea_perfil_de_colaborador(self):
        usuario = User.registrar({**DATOS_VALIDOS, "tipo_usuario": "cliente"})
        self.assertIsNone(usuario.perfil_colaborador)

    def test_la_contrasena_solo_se_guarda_como_hash(self):
        usuario = User.registrar(DATOS_VALIDOS)
        self.assertNotIn("clave-segura-1", usuario.password_hash)
        self.assertTrue(usuario.check_password("clave-segura-1"))
        self.assertFalse(usuario.check_password("otra-clave"))

    def test_campos_vacios_devuelven_todos_los_errores(self):
        vacios = {campo: "" for campo in DATOS_VALIDOS}
        with self.assertRaises(RegistroInvalido) as contexto:
            User.registrar(vacios)
        self.assertEqual(len(contexto.exception.errores), 4)

    def test_correos_invalidos_se_rechazan(self):
        for correo in ("", "sin-arroba", "a@b", "a b@c.com", "@c.com", "a@.com"):
            with self.subTest(correo=correo):
                with self.assertRaises(RegistroInvalido):
                    User.registrar({**DATOS_VALIDOS, "correo": correo})

    def test_contrasena_corta_se_rechaza(self):
        with self.assertRaises(RegistroInvalido):
            User.registrar({**DATOS_VALIDOS, "password": "corta"})

    def test_rol_invalido_se_rechaza_y_no_se_puede_crear_administrador(self):
        for rol in ("", "admin", "administrador", "superusuario"):
            with self.subTest(rol=rol):
                with self.assertRaises(RegistroInvalido):
                    User.registrar({**DATOS_VALIDOS, "tipo_usuario": rol})

    def test_correo_duplicado_se_rechaza_sin_importar_mayusculas(self):
        db.session.add(User.registrar(DATOS_VALIDOS))
        db.session.commit()
        with self.assertRaises(RegistroInvalido) as contexto:
            User.registrar({**DATOS_VALIDOS, "correo": "LUCIA@prueba.test", "nombre": "Otra"})
        self.assertIn("Ya existe una cuenta con ese correo.", contexto.exception.errores)

    def test_encapsulacion_un_user_no_puede_quedar_en_estado_invalido(self):
        usuario = User()
        with self.assertRaises(ValueError):
            usuario.correo = "no-es-un-correo"
        with self.assertRaises(ValueError):
            usuario.tipo_usuario = "admin"
        with self.assertRaises(ValueError):
            usuario.nombre = "   "
        with self.assertRaises(ValueError):
            usuario.set_password("corta")
        usuario.correo = "  OK@Prueba.test "
        self.assertEqual(usuario.correo, "ok@prueba.test")


class PruebasFlujoMVC(BaseApp):
    """Vista -> Controller -> Model -> Vista."""

    FORMULARIO = {
        "nombre": "Lucía Pérez",
        "correo": "lucia@prueba.test",
        "password": "clave-segura-1",
        "tipo_usuario": "colaborador",
    }

    def test_get_muestra_el_formulario(self):
        respuesta = self.cliente_anonimo().get("/registro")
        self.assertEqual(respuesta.status_code, 200)
        html = respuesta.get_data(as_text=True)
        for campo in ("nombre", "correo", "password", "tipo_usuario"):
            self.assertIn(f'name="{campo}"', html)

    def test_registro_valido_colaborador_persiste_inicia_sesion_y_va_al_panel(self):
        respuesta = self.cliente_anonimo().post("/registro", data=self.FORMULARIO)
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("/dashboard/", respuesta.headers["Location"])
        usuario = User.query.one()
        self.assertEqual(usuario.correo, "lucia@prueba.test")
        self.assertIsNotNone(usuario.perfil_colaborador)
        self.assertNotIn("clave-segura-1", usuario.password_hash)

    def test_registro_valido_cliente_va_al_inicio_sin_perfil(self):
        respuesta = self.cliente_anonimo().post("/registro", data={**self.FORMULARIO, "tipo_usuario": "cliente"})
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(respuesta.headers["Location"].endswith("/"))
        self.assertIsNone(User.query.one().perfil_colaborador)

    def test_datos_invalidos_devuelven_400_con_mensajes_y_conservan_lo_escrito(self):
        respuesta = self.cliente_anonimo().post(
            "/registro", data={**self.FORMULARIO, "correo": "malo", "password": "x", "tipo_usuario": "admin"}
        )
        html = respuesta.get_data(as_text=True)
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("correo electrónico válido", html)
        self.assertIn("al menos 8 caracteres", html)
        self.assertIn("Elegí si necesitás contratar", html)
        self.assertIn('value="Lucía Pérez"', html)  # conserva el nombre
        self.assertEqual(User.query.count(), 0)

    def test_correo_duplicado_devuelve_400_y_no_crea_otra_cuenta(self):
        self.cliente_anonimo().post("/registro", data=self.FORMULARIO)
        respuesta = self.cliente_anonimo().post("/registro", data=self.FORMULARIO)
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("Ya existe una cuenta", respuesta.get_data(as_text=True))
        self.assertEqual(User.query.count(), 1)

    def test_no_se_puede_registrar_un_administrador_por_el_formulario_publico(self):
        respuesta = self.cliente_anonimo().post("/registro", data={**self.FORMULARIO, "tipo_usuario": "administrador"})
        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(User.query.count(), 0)

    def test_usuario_registrado_puede_iniciar_sesion(self):
        self.cliente_anonimo().post("/registro", data=self.FORMULARIO)
        respuesta = self.cliente_anonimo().post("/login", data={"correo": "lucia@prueba.test", "password": "clave-segura-1"})
        self.assertEqual(respuesta.status_code, 302)


if __name__ == "__main__":
    unittest.main()
