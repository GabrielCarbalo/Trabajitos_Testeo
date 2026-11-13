"""
Pruebas de los avisos derivados (Aviso, CollaboratorProfile.avisos y
ResumenAdministracion en app/models.py) y de su aparición en los paneles.

Se ejecutan con:   python -m unittest tests.test_avisos -v
Usan una base de datos SQLite EN MEMORIA (ver tests/base.py).
"""

import unittest

from app import db
from app.models import (
    Aviso,
    Category,
    CollaboratorProfile,
    PortfolioImage,
    ResumenAdministracion,
    Service,
    User,
)
from tests.base import HASH_PASSWORD, BaseApp
from tests.test_servicios import _crear_colaborador


def _mensajes(perfil):
    return [a.mensaje for a in perfil.avisos()]


def _hay(perfil, fragmento):
    return any(fragmento in m for m in _mensajes(perfil))


def _foto(perfil, estado, n, motivo=None):
    perfil.portafolio.append(
        PortfolioImage(
            filename=f"{perfil.id}-{estado}-{n}.png", hash_exacto=f"{perfil.id}-{estado}-{n}",
            moderation_status=estado, moderation_reason=motivo,
        )
    )


class PruebasAvisosColaborador(BaseApp):
    def setUp(self):
        super().setUp()
        self.ana = _crear_colaborador("Ana", "ana@prueba.test", fotos_aprobadas=2)
        self.beto = _crear_colaborador("Beto", "beto@prueba.test", fotos_aprobadas=0)
        db.session.commit()

    def test_aviso_con_nivel_invalido_falla(self):
        with self.assertRaises(ValueError):
            Aviso(nivel="x", mensaje="hola")

    def test_descripcion_whatsapp_y_foto_faltantes_y_se_resuelven(self):
        self.ana.descripcion = None
        self.assertTrue(_hay(self.ana, "no tiene descripción"))
        self.assertTrue(_hay(self.ana, "botón de WhatsApp"))
        self.assertTrue(_hay(self.ana, "foto de perfil"))
        self.ana.descripcion = "Hola"
        self.ana.telefono_whatsapp = "+503 7123 4567"
        self.ana.foto_filename = "f.png"
        self.ana.foto_moderation_status = "approved"
        self.assertFalse(_hay(self.ana, "no tiene descripción"))
        self.assertFalse(_hay(self.ana, "WhatsApp"))
        self.assertFalse(_hay(self.ana, "foto de perfil"))
        self.assertTrue(self.ana.perfil_completo)

    def test_foto_de_perfil_rechazada_es_alerta_y_en_revision_es_info(self):
        self.ana.foto_filename = "f.png"
        self.ana.foto_moderation_status = "rejected"
        self.ana.foto_moderation_reason = "Borrosa"
        aviso = next(a for a in self.ana.avisos() if "foto de perfil fue rechazada" in a.mensaje)
        self.assertEqual(aviso.nivel, "alerta")
        self.assertIn("Borrosa", aviso.mensaje)

        self.ana.foto_moderation_status = "flagged"
        aviso = next(a for a in self.ana.avisos() if "foto de perfil está en revisión" in a.mensaje)
        self.assertEqual(aviso.nivel, "info")

    def test_faltan_fotos_aprobadas(self):
        self.assertTrue(_hay(self.beto, "Te faltan 2 fotos aprobadas"))
        self.assertFalse(_hay(self.ana, "Te faltan"))

    def test_fotos_rechazadas_son_alerta_y_en_revision_info(self):
        _foto(self.ana, "rejected", 1)
        _foto(self.ana, "flagged", 1)
        db.session.commit()
        rechazada = next(a for a in self.ana.avisos() if "rechazada" in a.mensaje)
        self.assertEqual(rechazada.nivel, "alerta")
        self.assertTrue(_hay(self.ana, "1 foto en revisión"))

    def test_maximo_de_fotos(self):
        for n in range(6):
            _foto(self.ana, "approved", n)
        db.session.commit()
        self.assertTrue(_hay(self.ana, "Llegaste al máximo de 8 fotos"))
        self.assertFalse(_hay(self.ana, "eliminá las rechazadas"))

    def test_sin_servicios_pero_con_fotos_sugiere_publicar(self):
        self.assertTrue(_hay(self.ana, "primer servicio"))
        self.assertFalse(_hay(self.beto, "primer servicio"))

    def test_las_alertas_van_primero(self):
        niveles = [a.nivel for a in self.beto.avisos()]
        self.assertEqual(niveles, sorted(niveles, key=lambda n: n != "alerta"))

    def test_el_panel_de_ana_no_muestra_las_condiciones_de_beto(self):
        cliente = self.app.test_client()
        cliente.post("/login", data={"correo": "ana@prueba.test", "password": "password123"})
        html = cliente.get("/dashboard/").get_data(as_text=True)
        self.assertNotIn("Te faltan", html)
        self.assertIn("primer servicio", html)

    def test_el_panel_muestra_servicio_inactivo(self):
        categoria = Category(nombre="Limpieza", slug="limpieza")
        db.session.add(categoria)
        db.session.flush()
        db.session.add(
            Service(
                collaborator_profile_id=self.ana.id, category_id=categoria.id, titulo="Servicio pausado",
                descripcion="x", precio="10", modalidad="hora", disponibilidad="Siempre", activo=False,
            )
        )
        db.session.commit()
        cliente = self.app.test_client()
        cliente.post("/login", data={"correo": "ana@prueba.test", "password": "password123"})
        self.assertIn("Inactivo", cliente.get("/dashboard/").get_data(as_text=True))


class PruebasResumenAdministracion(BaseApp):
    def setUp(self):
        super().setUp()
        self.admin = User(nombre="Admin", correo="admin@prueba.test", tipo_usuario="cliente", password_hash=HASH_PASSWORD, es_admin=True)
        self.cliente = User(nombre="Cli", correo="cli@prueba.test", tipo_usuario="cliente", password_hash=HASH_PASSWORD)
        self.ana = _crear_colaborador("Ana", "ana@prueba.test", fotos_aprobadas=2)
        db.session.add_all([self.admin, self.cliente])
        db.session.commit()

    def test_conteos_y_clientes_excluyen_admin(self):
        resumen = ResumenAdministracion()
        self.assertEqual(resumen.cuentas, 3)
        self.assertEqual(resumen.clientes, 1)
        self.assertEqual(resumen.colaboradores, 1)
        self.assertEqual(resumen.administradores, 1)
        self.assertEqual(resumen.servicios_visibles, 0)

    def test_sin_cola_no_hay_avisos(self):
        self.assertEqual(ResumenAdministracion().avisos(), [])

    def test_fotos_en_revision_generan_alerta_con_cantidad(self):
        _foto(self.ana, "flagged", 1)
        self.ana.foto_filename, self.ana.foto_moderation_status = "f.png", "pending"
        db.session.commit()
        resumen = ResumenAdministracion()
        self.assertEqual(resumen.fotos_en_revision, 2)
        aviso = resumen.avisos()[0]
        self.assertEqual(aviso.nivel, "alerta")
        self.assertIn("2 fotos", aviso.mensaje)
        self.assertEqual(aviso.destino, "admin.fotos")

    def test_aviso_de_suspendidas_enlaza_al_filtro(self):
        self.cliente.banear()
        db.session.commit()
        aviso = ResumenAdministracion().avisos()[0]
        self.assertEqual(aviso.nivel, "info")
        cliente = self.app.test_client()
        cliente.post("/login", data={"correo": "admin@prueba.test", "password": "password123"})
        html = cliente.get("/admin/").get_data(as_text=True)
        self.assertIn("/admin/cuentas?estado=banned", html)


if __name__ == "__main__":
    unittest.main()
