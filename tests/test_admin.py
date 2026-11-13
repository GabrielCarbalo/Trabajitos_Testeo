"""
Pruebas del módulo "Administración": permisos, suspender/reactivar cuentas,
moderar fotos en revisión y el comando "flask crear-admin".

Se ejecutan con:   python -m unittest tests.test_admin -v
Usan una base de datos SQLite EN MEMORIA: no tocan instance/trabajitos.db.
"""

import unittest

from flask import g

from app import db
from app.models import (
    MOTIVO_RECHAZO_POR_DEFECTO,
    AccionNoPermitida,
    Category,
    CollaboratorProfile,
    PortfolioImage,
    Service,
    User,
)
from tests.base import HASH_PASSWORD, BaseApp


class BaseAdmin(BaseApp):
    """Un admin, un colaborador con un servicio publicado y fotos en distintos estados, y un cliente."""

    def setUp(self):
        super().setUp()
        self.admin = User(
            nombre="Admin", correo="admin@prueba.test", tipo_usuario="cliente", password_hash=HASH_PASSWORD, es_admin=True
        )
        self.ana = User(nombre="Ana", correo="ana@prueba.test", tipo_usuario="colaborador", password_hash=HASH_PASSWORD)
        self.perfil = CollaboratorProfile(
            usuario=self.ana,
            descripcion="Perfil de prueba",
            foto_filename="perfil.png",
            foto_hash="h-perfil",
            foto_moderation_status="flagged",
            foto_moderation_reason="Coincide con otra cuenta.",
        )
        self.foto_en_revision = PortfolioImage(filename="p1.png", hash_exacto="h1", moderation_status="flagged")
        self.foto_aprobada = PortfolioImage(filename="p2.png", hash_exacto="h2", moderation_status="approved")
        self.perfil.portafolio.append(self.foto_en_revision)
        self.perfil.portafolio.append(self.foto_aprobada)
        self.cliente = User(nombre="Cliente", correo="cliente@prueba.test", tipo_usuario="cliente", password_hash=HASH_PASSWORD)

        categoria = Category(nombre="Limpieza", slug="limpieza")
        db.session.add_all([self.admin, self.ana, self.cliente, categoria])
        db.session.flush()
        db.session.add(
            Service(
                collaborator_profile_id=self.perfil.id,
                category_id=categoria.id,
                titulo="Limpieza de casas",
                descripcion="Limpieza completa.",
                precio="20",
                modalidad="hora",
                disponibilidad="Lunes a viernes",
            )
        )
        db.session.commit()

    def entrar_como(self, correo):
        g.pop("_login_user", None)
        cliente = self.app.test_client()
        respuesta = cliente.post("/login", data={"correo": correo, "password": "password123"})
        self.assertEqual(respuesta.status_code, 302)
        return cliente


class PruebasModelo(BaseAdmin):
    def test_un_admin_no_se_puede_suspender(self):
        with self.assertRaises(AccionNoPermitida):
            self.admin.banear()
        self.assertFalse(self.admin.esta_baneado)

    def test_banear_y_reactivar(self):
        self.ana.banear()
        self.assertTrue(self.ana.esta_baneado)
        self.ana.reactivar()
        self.assertFalse(self.ana.esta_baneado)

    def test_rechazar_sin_motivo_usa_el_texto_por_defecto(self):
        self.foto_en_revision.rechazar("   ")
        self.assertEqual(self.foto_en_revision.moderation_status, "rejected")
        self.assertEqual(self.foto_en_revision.moderation_reason, MOTIVO_RECHAZO_POR_DEFECTO)

    def test_motivo_demasiado_largo_no_cambia_la_foto(self):
        with self.assertRaises(ValueError):
            self.perfil.rechazar_foto("x" * 256)
        self.assertEqual(self.perfil.foto_moderation_status, "flagged")

    def test_aprobar_borra_el_motivo_anterior(self):
        self.perfil.aprobar_foto()
        self.assertEqual(self.perfil.foto_moderation_status, "approved")
        self.assertIsNone(self.perfil.foto_moderation_reason)


class PruebasPermisos(BaseAdmin):
    URLS = ("/admin/", "/admin/fotos", "/admin/cuentas")

    def test_anonimo_va_al_login(self):
        for url in self.URLS:
            with self.subTest(url=url):
                respuesta = self.cliente_anonimo().get(url)
                self.assertEqual(respuesta.status_code, 302)
                self.assertIn("/login", respuesta.headers["Location"])

    def test_cliente_y_colaborador_reciben_403(self):
        for correo in ("cliente@prueba.test", "ana@prueba.test"):
            cliente = self.entrar_como(correo)
            for url in self.URLS:
                with self.subTest(correo=correo, url=url):
                    self.assertEqual(cliente.get(url).status_code, 403)
            respuesta = cliente.post(f"/admin/cuentas/{self.cliente.id}/banear")
            self.assertEqual(respuesta.status_code, 403)
        db.session.refresh(self.cliente)
        self.assertFalse(self.cliente.esta_baneado)

    def test_admin_ve_todas_las_paginas_y_el_link_en_el_header(self):
        cliente = self.entrar_como("admin@prueba.test")
        for url in self.URLS:
            with self.subTest(url=url):
                self.assertEqual(cliente.get(url).status_code, 200)
        self.assertIn("Administración", cliente.get("/").get_data(as_text=True))

    def test_login_de_admin_lleva_al_panel_de_administracion(self):
        respuesta = self.cliente_anonimo().post(
            "/login", data={"correo": "admin@prueba.test", "password": "password123"}
        )
        self.assertTrue(respuesta.headers["Location"].endswith("/admin/"))

    def test_el_registro_publico_ignora_un_es_admin_inyectado(self):
        self.cliente_anonimo().post(
            "/registro",
            data={
                "nombre": "Pícaro",
                "correo": "picaro@prueba.test",
                "password": "password123",
                "tipo_usuario": "cliente",
                "es_admin": "1",
            },
        )
        self.assertFalse(User.query.filter_by(correo="picaro@prueba.test").one().es_admin)


class PruebasCuentas(BaseAdmin):
    def test_suspender_oculta_sus_servicios_y_reactivar_los_devuelve(self):
        admin = self.entrar_como("admin@prueba.test")
        self.assertEqual(admin.post(f"/admin/cuentas/{self.ana.id}/banear").status_code, 302)
        db.session.refresh(self.ana)
        self.assertTrue(self.ana.esta_baneado)
        self.assertNotIn("Limpieza de casas", self.cliente_anonimo().get("/explorar").get_data(as_text=True))

        admin = self.entrar_como("admin@prueba.test")
        admin.post(f"/admin/cuentas/{self.ana.id}/reactivar")
        db.session.refresh(self.ana)
        self.assertFalse(self.ana.esta_baneado)
        self.assertIn("Limpieza de casas", self.cliente_anonimo().get("/explorar").get_data(as_text=True))

    def test_admin_no_se_puede_suspender_a_si_mismo(self):
        admin = self.entrar_como("admin@prueba.test")
        respuesta = admin.post(f"/admin/cuentas/{self.admin.id}/banear", follow_redirects=True)
        self.assertIn("No se puede suspender una cuenta de administrador.", respuesta.get_data(as_text=True))
        db.session.refresh(self.admin)
        self.assertFalse(self.admin.esta_baneado)

    def test_buscar_y_filtrar_cuentas(self):
        self.ana.banear()
        db.session.commit()
        admin = self.entrar_como("admin@prueba.test")

        html = admin.get("/admin/cuentas?q=ana@").get_data(as_text=True)
        self.assertIn("ana@prueba.test", html)
        self.assertNotIn("cliente@prueba.test", html)

        html = admin.get("/admin/cuentas?estado=banned").get_data(as_text=True)
        self.assertIn("ana@prueba.test", html)
        self.assertNotIn("cliente@prueba.test", html)

    def test_despues_de_suspender_vuelve_a_la_misma_busqueda(self):
        admin = self.entrar_como("admin@prueba.test")
        respuesta = admin.post(f"/admin/cuentas/{self.cliente.id}/banear", data={"q": "cli", "estado": "active"})
        self.assertIn("/admin/cuentas?q=cli&estado=active", respuesta.headers["Location"])

    def test_id_inexistente_da_404(self):
        admin = self.entrar_como("admin@prueba.test")
        self.assertEqual(admin.post("/admin/cuentas/9999/banear").status_code, 404)
        self.assertEqual(admin.post("/admin/fotos/portafolio/9999/aprobar").status_code, 404)


class PruebasFotos(BaseAdmin):
    def test_la_cola_muestra_solo_fotos_en_revision(self):
        html = self.entrar_como("admin@prueba.test").get("/admin/fotos").get_data(as_text=True)
        self.assertIn("perfil.png", html)
        self.assertIn("p1.png", html)
        self.assertNotIn("p2.png", html)

    def test_aprobar_foto_de_portafolio_la_hace_publica(self):
        admin = self.entrar_como("admin@prueba.test")
        admin.post(f"/admin/fotos/portafolio/{self.foto_en_revision.id}/aprobar")
        db.session.refresh(self.foto_en_revision)
        self.assertEqual(self.foto_en_revision.moderation_status, "approved")
        html = self.cliente_anonimo().get(f"/colaborador/{self.perfil.id}").get_data(as_text=True)
        self.assertIn("p1.png", html)

    def test_rechazar_foto_de_portafolio_guarda_el_motivo(self):
        admin = self.entrar_como("admin@prueba.test")
        admin.post(f"/admin/fotos/portafolio/{self.foto_en_revision.id}/rechazar", data={"motivo": "Foto borrosa."})
        db.session.refresh(self.foto_en_revision)
        self.assertEqual(self.foto_en_revision.moderation_status, "rejected")
        self.assertEqual(self.foto_en_revision.moderation_reason, "Foto borrosa.")

    def test_aprobar_y_rechazar_foto_de_perfil(self):
        admin = self.entrar_como("admin@prueba.test")
        admin.post(f"/admin/fotos/perfil/{self.perfil.id}/rechazar", data={"motivo": ""})
        db.session.refresh(self.perfil)
        self.assertEqual(self.perfil.foto_moderation_status, "rejected")
        self.assertEqual(self.perfil.foto_moderation_reason, MOTIVO_RECHAZO_POR_DEFECTO)

        admin.post(f"/admin/fotos/perfil/{self.perfil.id}/aprobar")
        db.session.refresh(self.perfil)
        self.assertTrue(self.perfil.foto_visible)

    def test_motivo_demasiado_largo_muestra_error_y_no_rechaza(self):
        admin = self.entrar_como("admin@prueba.test")
        respuesta = admin.post(
            f"/admin/fotos/perfil/{self.perfil.id}/rechazar", data={"motivo": "x" * 300}, follow_redirects=True
        )
        self.assertIn("El motivo no puede tener más de 255 caracteres.", respuesta.get_data(as_text=True))
        db.session.refresh(self.perfil)
        self.assertEqual(self.perfil.foto_moderation_status, "flagged")

    def test_perfil_sin_foto_da_404(self):
        self.perfil.foto_filename = None
        db.session.commit()
        admin = self.entrar_como("admin@prueba.test")
        self.assertEqual(admin.post(f"/admin/fotos/perfil/{self.perfil.id}/aprobar").status_code, 404)


class PruebasComandoCrearAdmin(BaseApp):
    def ejecutar(self, *argumentos):
        return self.app.test_cli_runner().invoke(args=["crear-admin", *argumentos])

    def test_crea_un_admin_valido(self):
        resultado = self.ejecutar("--nombre", "Gabriel", "--correo", "Gabo@Prueba.test", "--password", "clave-segura-1")
        self.assertEqual(resultado.exit_code, 0, resultado.output)
        usuario = User.query.filter_by(correo="gabo@prueba.test").one()
        self.assertTrue(usuario.es_admin)
        self.assertTrue(usuario.check_password("clave-segura-1"))

    def test_rechaza_datos_invalidos_y_correo_repetido(self):
        self.assertNotEqual(self.ejecutar("--nombre", "X", "--correo", "malo", "--password", "corta").exit_code, 0)
        self.ejecutar("--nombre", "X", "--correo", "x@prueba.test", "--password", "clave-segura-1")
        resultado = self.ejecutar("--nombre", "Y", "--correo", "x@prueba.test", "--password", "clave-segura-1")
        self.assertNotEqual(resultado.exit_code, 0)
        self.assertIn("Ya existe una cuenta con ese correo.", resultado.output)
        self.assertEqual(User.query.count(), 1)


if __name__ == "__main__":
    unittest.main()
