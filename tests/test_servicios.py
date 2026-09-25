"""
Pruebas del módulo "Gestión de servicios" (MVC + POO).

Se ejecutan con:   python -m unittest tests.test_servicios -v
Usan una base de datos SQLite EN MEMORIA: no tocan instance/trabajitos.db.

Dos grupos:
  - PruebasModelo: la clase Service / CollaboratorProfile por sí solas (POO).
  - PruebasFlujoMVC: el recorrido completo Vista -> Controller -> Model -> Vista
    usando el cliente de pruebas de Flask.
"""

import io
import os
import unittest
from decimal import Decimal

from flask import g

from app import db
from app.models import (
    Category,
    CollaboratorProfile,
    PortafolioInsuficiente,
    PortfolioImage,
    Service,
    ServicioInvalido,
    User,
)
from tests.base import HASH_PASSWORD, BaseApp

DATOS_VALIDOS = {
    "titulo": "Pintura de interiores",
    "descripcion": "Pinto habitaciones con acabado prolijo.",
    "categoria_id": "1",
    "modalidad": "tarea",
    "precio": "45",
    "disponibilidad": "Fines de semana",
}


def _crear_colaborador(nombre, correo, fotos_aprobadas):
    usuario = User(nombre=nombre, correo=correo, tipo_usuario="colaborador", password_hash=HASH_PASSWORD)
    perfil = CollaboratorProfile(usuario=usuario, descripcion="Perfil de prueba")
    for i in range(fotos_aprobadas):
        perfil.portafolio.append(
            PortfolioImage(filename=f"{correo}-{i}.png", hash_exacto=f"{correo}-{i}", moderation_status="approved")
        )
    db.session.add(usuario)
    return perfil


class BaseConApp(BaseApp):
    """App limpia (tests/base.py) + los datos de prueba propios del módulo Servicios."""

    def setUp(self):
        super().setUp()
        db.session.add_all([Category(nombre="Limpieza", slug="limpieza"), Category(nombre="Otros", slug="otros")])
        self.ana = _crear_colaborador("Ana Con Portafolio", "ana@prueba.test", fotos_aprobadas=2)
        self.beto = _crear_colaborador("Beto Sin Portafolio", "beto@prueba.test", fotos_aprobadas=0)
        self.carla = _crear_colaborador("Carla Con Portafolio", "carla@prueba.test", fotos_aprobadas=2)
        db.session.add(User(nombre="Cliente", correo="cliente@prueba.test", tipo_usuario="cliente", password_hash=HASH_PASSWORD))
        db.session.commit()


class PruebasModelo(BaseConApp):
    """POO: la clase Service protege sus propias reglas, sin pasar por ningún formulario."""

    def test_datos_validos_se_normalizan(self):
        limpios = Service.validar_datos({**DATOS_VALIDOS, "titulo": "  Pintura  "})
        self.assertEqual(limpios["titulo"], "Pintura")
        self.assertEqual(limpios["precio"], Decimal("45.00"))
        self.assertEqual(limpios["category_id"], 1)

    def test_campos_obligatorios_vacios_devuelven_todos_los_errores(self):
        vacios = {campo: "" for campo in DATOS_VALIDOS}
        with self.assertRaises(ServicioInvalido) as contexto:
            Service.validar_datos(vacios)
        self.assertEqual(len(contexto.exception.errores), 6)

    def test_precio_invalido_se_rechaza(self):
        for precio in ("", "abc", "0", "-5", "nan", "inf", "9999999"):
            with self.subTest(precio=precio):
                with self.assertRaises(ServicioInvalido):
                    Service.validar_datos({**DATOS_VALIDOS, "precio": precio})

    def test_categoria_inexistente_se_rechaza(self):
        with self.assertRaises(ServicioInvalido):
            Service.validar_datos({**DATOS_VALIDOS, "categoria_id": "999"})

    def test_categoria_con_formato_raro_se_rechaza_sin_romper(self):
        # "²" pasa str.isdigit() pero int() no lo convierte, y un número enorme
        # no entra en un INTEGER de SQLite: antes ambos terminaban en error 500.
        for categoria_id in ("²", "٣", "9" * 25, "-1", "1.0"):
            with self.subTest(categoria_id=categoria_id):
                with self.assertRaises(ServicioInvalido):
                    Service.validar_datos({**DATOS_VALIDOS, "categoria_id": categoria_id})

    def test_modalidad_y_longitudes(self):
        with self.assertRaises(ServicioInvalido):
            Service.validar_datos({**DATOS_VALIDOS, "modalidad": "semana"})
        with self.assertRaises(ServicioInvalido):
            Service.validar_datos({**DATOS_VALIDOS, "titulo": "x" * (Service.LONGITUD_MAXIMA_TITULO + 1)})

    def test_encapsulacion_un_servicio_no_puede_quedar_en_estado_invalido(self):
        servicio = Service()
        with self.assertRaises(ValueError):
            servicio.precio = -1
        with self.assertRaises(ValueError):
            servicio.titulo = "   "
        servicio.precio = 15.5
        self.assertEqual(servicio.precio, Decimal("15.50"))

    def test_pertenece_a_solo_reconoce_al_dueno(self):
        servicio = self.ana.publicar_servicio(DATOS_VALIDOS)
        db.session.add(servicio)
        db.session.commit()
        self.assertTrue(servicio.pertenece_a(self.ana))
        self.assertFalse(servicio.pertenece_a(self.carla))
        self.assertFalse(servicio.pertenece_a(None))

    def test_publicar_sin_portafolio_minimo_lanza_excepcion_de_dominio(self):
        with self.assertRaises(PortafolioInsuficiente):
            self.beto.publicar_servicio(DATOS_VALIDOS)

    def test_actualizar_invalido_no_modifica_el_objeto(self):
        servicio = self.ana.publicar_servicio(DATOS_VALIDOS)
        db.session.add(servicio)
        db.session.commit()
        with self.assertRaises(ServicioInvalido):
            servicio.actualizar({**DATOS_VALIDOS, "titulo": "Nuevo titulo", "precio": "-1"})
        self.assertEqual(servicio.titulo, "Pintura de interiores")


class PruebasFlujoMVC(BaseConApp):
    """Vista -> Controller -> Model -> Vista, con el cliente de pruebas de Flask."""

    def entrar_como(self, correo):
        cliente = self.app.test_client()
        respuesta = cliente.post("/login", data={"correo": correo, "password": "password123"})
        self.assertEqual(respuesta.status_code, 302)
        return cliente

    def test_get_formulario_para_colaborador_con_portafolio(self):
        respuesta = self.entrar_como("ana@prueba.test").get("/dashboard/servicios/nuevo")
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("Precio referencial", respuesta.get_data(as_text=True))

    def test_get_sin_portafolio_muestra_pantalla_de_requisito(self):
        respuesta = self.entrar_como("beto@prueba.test").get("/dashboard/servicios/nuevo")
        self.assertIn("Necesitás fotos", respuesta.get_data(as_text=True))

    def test_publicar_servicio_valido_persiste_y_se_muestra_en_catalogo_y_perfil(self):
        cliente = self.entrar_como("ana@prueba.test")
        respuesta = cliente.post("/dashboard/servicios/nuevo", data=DATOS_VALIDOS)
        self.assertEqual(respuesta.status_code, 302)  # redirect al panel

        servicio = Service.query.one()
        self.assertEqual(servicio.titulo, "Pintura de interiores")
        self.assertTrue(servicio.pertenece_a(self.ana))

        anonimo = self.app.test_client()
        self.assertIn("Pintura de interiores", anonimo.get("/explorar").get_data(as_text=True))
        self.assertIn("Pintura de interiores", anonimo.get(f"/colaborador/{self.ana.id}").get_data(as_text=True))

    def test_campo_obligatorio_vacio_no_crea_y_muestra_error(self):
        respuesta = self.entrar_como("ana@prueba.test").post(
            "/dashboard/servicios/nuevo", data={**DATOS_VALIDOS, "titulo": ""}
        )
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("Ponele un título", respuesta.get_data(as_text=True))
        self.assertEqual(Service.query.count(), 0)

    def test_precio_invalido_no_crea(self):
        respuesta = self.entrar_como("ana@prueba.test").post(
            "/dashboard/servicios/nuevo", data={**DATOS_VALIDOS, "precio": "nan"}
        )
        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(Service.query.count(), 0)

    def test_categoria_invalida_no_crea(self):
        respuesta = self.entrar_como("ana@prueba.test").post(
            "/dashboard/servicios/nuevo", data={**DATOS_VALIDOS, "categoria_id": "999"}
        )
        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(Service.query.count(), 0)

    def test_post_directo_sin_portafolio_minimo_no_crea(self):
        respuesta = self.entrar_como("beto@prueba.test").post("/dashboard/servicios/nuevo", data=DATOS_VALIDOS)
        self.assertIn("Necesitás fotos", respuesta.get_data(as_text=True))
        self.assertEqual(Service.query.count(), 0)

    def test_editar_servicio_propio_actualiza_los_datos(self):
        servicio = self.ana.publicar_servicio(DATOS_VALIDOS)
        db.session.add(servicio)
        db.session.commit()

        respuesta = self.entrar_como("ana@prueba.test").post(
            f"/dashboard/servicios/{servicio.id}/editar", data={**DATOS_VALIDOS, "precio": "60", "titulo": "Pintura pro"}
        )
        self.assertEqual(respuesta.status_code, 302)
        db.session.refresh(servicio)
        self.assertEqual(servicio.titulo, "Pintura pro")
        self.assertEqual(servicio.precio, Decimal("60.00"))

    def test_editar_servicio_ajeno_es_rechazado_y_no_cambia_nada(self):
        servicio = self.ana.publicar_servicio(DATOS_VALIDOS)
        db.session.add(servicio)
        db.session.commit()

        cliente_carla = self.entrar_como("carla@prueba.test")
        self.assertEqual(cliente_carla.get(f"/dashboard/servicios/{servicio.id}/editar").status_code, 403)
        respuesta = cliente_carla.post(f"/dashboard/servicios/{servicio.id}/editar", data={**DATOS_VALIDOS, "titulo": "Hackeado"})
        self.assertEqual(respuesta.status_code, 403)
        db.session.refresh(servicio)
        self.assertEqual(servicio.titulo, "Pintura de interiores")

    def test_ids_enormes_en_la_url_dan_404_y_no_error_500(self):
        cliente = self.entrar_como("ana@prueba.test")
        enorme = "9" * 25
        self.assertEqual(cliente.get(f"/colaborador/{enorme}").status_code, 404)
        self.assertEqual(cliente.get(f"/dashboard/servicios/{enorme}/editar").status_code, 404)
        self.assertEqual(cliente.post(f"/dashboard/portafolio/{enorme}/eliminar").status_code, 404)

    def test_telefono_con_pocos_digitos_se_rechaza(self):
        cliente = self.entrar_como("ana@prueba.test")
        for telefono in ("1       2", "+  1234  ", "٧١٢٣٤٥٦٧"):
            with self.subTest(telefono=telefono):
                respuesta = cliente.post("/dashboard/perfil", data={"descripcion": "Hola", "telefono_whatsapp": telefono})
                self.assertEqual(respuesta.status_code, 400)
        respuesta = cliente.post("/dashboard/perfil", data={"descripcion": "Hola", "telefono_whatsapp": "+503 7123 4567"})
        self.assertEqual(respuesta.status_code, 302)
        db.session.refresh(self.ana)
        self.assertEqual(self.ana.telefono_whatsapp, "+503 7123 4567")

    def test_foto_de_perfil_no_queda_huerfana_si_el_formulario_falla(self):
        carpeta = os.path.join(self.app.static_folder, "uploads", "profile")
        os.makedirs(carpeta, exist_ok=True)
        antes = set(os.listdir(carpeta))
        png = b"\x89PNG\r\n\x1a\n" + b"0" * 32
        respuesta = self.entrar_como("ana@prueba.test").post(
            "/dashboard/perfil",
            data={"descripcion": "", "foto": (io.BytesIO(png), "foto.png")},
            content_type="multipart/form-data",
        )
        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(set(os.listdir(carpeta)), antes)

    def test_permisos_cliente_y_anonimo(self):
        self.assertEqual(self.entrar_como("cliente@prueba.test").get("/dashboard/servicios/nuevo").status_code, 403)
        # Estas pruebas mantienen un app_context abierto, y Flask lo reutiliza en
        # cada request: hay que borrar el usuario que Flask-Login dejó en caché
        # (g) para simular de verdad a una persona sin sesión.
        g.pop("_login_user", None)
        anonimo = self.app.test_client().get("/dashboard/servicios/nuevo")
        self.assertEqual(anonimo.status_code, 302)
        self.assertIn("/login", anonimo.headers["Location"])


if __name__ == "__main__":
    unittest.main()
