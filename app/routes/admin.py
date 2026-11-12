"""
Panel de administración: suspender o reactivar cuentas, y aprobar o
rechazar las fotografías que quedaron en revisión.

Todas las rutas requieren sesión iniciada Y una cuenta con es_admin. Igual
que en el panel del colaborador, esa regla se aplica una sola vez con un
before_request. Las REGLAS (no se puede suspender a un admin, largo del
motivo de rechazo) viven en los modelos (app/models.py); este archivo solo
lee la petición, llama al Model y decide qué mostrar.
"""

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from app import db
from app.models import (
    ACCOUNT_STATUSES,
    ESTADOS_EN_REVISION,
    AccionNoPermitida,
    CollaboratorProfile,
    PortfolioImage,
    ResumenAdministracion,
    User,
)
from app.routes.main import _escapar_like
from app.services.image_storage import storage
from app.services.uploads import SUBCARPETA_PERFIL

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

CUENTAS_POR_PAGINA = 25
# Tope del número de página: un ?page= gigante generaba un OFFSET que no
# entra en un entero de la base (error 500). Pasado el tope la lista sale vacía.
PAGINA_MAXIMA = 100_000


@admin_bp.before_request
@login_required
def restringir_a_administradores():
    """login_required corre primero (sin sesión -> /login); sin permiso de admin -> 403."""
    if not current_user.es_admin:
        abort(403)


def _fotos_de_perfil_en_revision():
    return (
        CollaboratorProfile.query.filter(
            CollaboratorProfile.foto_filename.isnot(None),
            CollaboratorProfile.foto_moderation_status.in_(ESTADOS_EN_REVISION),
        )
        .order_by(CollaboratorProfile.id)
        .all()
    )


def _fotos_de_portafolio_en_revision():
    return (
        PortfolioImage.query.filter(PortfolioImage.moderation_status.in_(ESTADOS_EN_REVISION))
        .order_by(PortfolioImage.fecha_subida)
        .all()
    )


@admin_bp.route("/")
def index():
    """Resumen: fotos esperando revisión, cuentas por tipo y estado, y avisos pendientes."""
    resumen = ResumenAdministracion()
    return render_template("admin/panel.html", resumen=resumen, avisos=resumen.avisos())


# ----------------------------------------------------------------------
# FOTOS EN REVISIÓN
# ----------------------------------------------------------------------
@admin_bp.route("/fotos")
def fotos():
    perfiles = _fotos_de_perfil_en_revision()
    return render_template(
        "admin/fotos.html",
        perfiles=[(perfil, storage.url(perfil.foto_filename, SUBCARPETA_PERFIL)) for perfil in perfiles],
        portafolio=_fotos_de_portafolio_en_revision(),
    )


def _rechazar(metodo_rechazo):
    """Aplica el rechazo con el motivo del formulario; si el motivo no es válido, avisa sin cambiar nada."""
    try:
        metodo_rechazo(request.form.get("motivo", ""))
    except ValueError as error:
        flash(str(error), "error")
        return False
    db.session.commit()
    return True


@admin_bp.route("/fotos/perfil/<int:perfil_id>/aprobar", methods=["POST"])
def aprobar_foto_perfil(perfil_id):
    perfil = db.get_or_404(CollaboratorProfile, perfil_id)
    if not perfil.foto_filename:
        abort(404)
    perfil.aprobar_foto()
    db.session.commit()
    flash(f"Aprobaste la foto de perfil de {perfil.usuario.nombre}.", "success")
    return redirect(url_for("admin.fotos"))


@admin_bp.route("/fotos/perfil/<int:perfil_id>/rechazar", methods=["POST"])
def rechazar_foto_perfil(perfil_id):
    perfil = db.get_or_404(CollaboratorProfile, perfil_id)
    if not perfil.foto_filename:
        abort(404)
    if _rechazar(perfil.rechazar_foto):
        flash(f"Rechazaste la foto de perfil de {perfil.usuario.nombre}.", "success")
    return redirect(url_for("admin.fotos"))


@admin_bp.route("/fotos/portafolio/<int:foto_id>/aprobar", methods=["POST"])
def aprobar_foto_portafolio(foto_id):
    foto = db.get_or_404(PortfolioImage, foto_id)
    foto.aprobar()
    db.session.commit()
    flash(f"Aprobaste una foto del portafolio de {foto.perfil.usuario.nombre}.", "success")
    return redirect(url_for("admin.fotos"))


@admin_bp.route("/fotos/portafolio/<int:foto_id>/rechazar", methods=["POST"])
def rechazar_foto_portafolio(foto_id):
    foto = db.get_or_404(PortfolioImage, foto_id)
    if _rechazar(foto.rechazar):
        flash(f"Rechazaste una foto del portafolio de {foto.perfil.usuario.nombre}.", "success")
    return redirect(url_for("admin.fotos"))


# ----------------------------------------------------------------------
# CUENTAS
# ----------------------------------------------------------------------
def _filtros_cuentas(fuente):
    """Lee búsqueda y estado (de la querystring o de los campos ocultos de un formulario)."""
    q = fuente.get("q", "").strip()
    estado = fuente.get("estado", "").strip()
    return q, (estado if estado in ACCOUNT_STATUSES else "")


@admin_bp.route("/cuentas")
def cuentas():
    q, estado = _filtros_cuentas(request.args)
    consulta = User.query
    if q:
        patron = f"%{_escapar_like(q)}%"
        consulta = consulta.filter(
            or_(User.nombre.ilike(patron, escape="\\"), User.correo.ilike(patron, escape="\\"))
        )
    if estado:
        consulta = consulta.filter(User.account_status == estado)

    # ?page= no numérico o menor a 1 -> página 1 (igual que paginate con error_out=False).
    numero_pagina = request.args.get("page", 1, type=int)
    numero_pagina = min(numero_pagina, PAGINA_MAXIMA) if numero_pagina and numero_pagina > 0 else 1
    pagina = consulta.order_by(User.fecha_creacion.desc(), User.id.desc()).paginate(
        page=numero_pagina, per_page=CUENTAS_POR_PAGINA, error_out=False
    )
    return render_template("admin/cuentas.html", pagina=pagina, q=q, estado=estado)


def _volver_a_cuentas():
    """Después de banear/reactivar, vuelve a la misma búsqueda en la que estaba el admin."""
    q, estado = _filtros_cuentas(request.form)
    return redirect(url_for("admin.cuentas", q=q or None, estado=estado or None))


@admin_bp.route("/cuentas/<int:user_id>/banear", methods=["POST"])
def banear_cuenta(user_id):
    usuario = db.get_or_404(User, user_id)
    try:
        usuario.banear()
    except AccionNoPermitida as error:
        flash(str(error), "error")
        return _volver_a_cuentas()
    db.session.commit()
    flash(f"Suspendiste la cuenta de {usuario.nombre}.", "success")
    return _volver_a_cuentas()


@admin_bp.route("/cuentas/<int:user_id>/reactivar", methods=["POST"])
def reactivar_cuenta(user_id):
    usuario = db.get_or_404(User, user_id)
    usuario.reactivar()
    db.session.commit()
    flash(f"Reactivaste la cuenta de {usuario.nombre}.", "success")
    return _volver_a_cuentas()
