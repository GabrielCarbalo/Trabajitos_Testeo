"""
Panel privado del colaborador: ver/editar su perfil (incluida la foto),
administrar su portafolio de trabajos, y publicar/editar servicios.

Todas las rutas de este blueprint son privadas: requieren sesión iniciada
Y que la cuenta sea de tipo "colaborador" (un cliente no tiene panel). Esa
regla se aplica una sola vez, con un before_request, en vez de repetirla en
cada ruta.
"""

import re

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, logout_user
from sqlalchemy.orm import joinedload

from app import db
from app.models import (
    MAXIMO_FOTOS_PORTAFOLIO,
    MINIMO_FOTOS_PORTAFOLIO_PARA_PUBLICAR,
    Category,
    CollaboratorProfile,
    PortafolioInsuficiente,
    PortfolioImage,
    Service,
    ServicioInvalido,
)
from app.services.image_storage import storage
from app.services.uploads import (
    SUBCARPETA_PERFIL,
    SUBCARPETA_PORTAFOLIO,
    ImagenInvalida,
    procesar_imagen_subida,
)

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

LONGITUD_MAXIMA_TELEFONO = 20
LONGITUD_MAXIMA_DESCRIPCION_PORTAFOLIO = 200

# Campos del formulario de servicio. Las reglas de cada uno (longitudes,
# rango de precio, modalidades válidas) están en la clase Service (Model).
CAMPOS_SERVICIO = ("titulo", "descripcion", "categoria_id", "modalidad", "precio", "disponibilidad")

# Acepta un "+" inicial opcional y entre 8 y 20 dígitos/espacios: cubre
# formatos como "+503 7123 4567" o "71234567" sin dejar pasar texto suelto.
# [0-9] y no \d: \d también acepta dígitos de otros alfabetos (ej. "٧"),
# que wa.me no entiende. Además se exige un mínimo de dígitos reales (ver
# _telefono_valido), porque el patrón solo no impide "1       2".
PATRON_TELEFONO = re.compile(r"^\+?[0-9 ]{8,20}$")
MINIMO_DIGITOS_TELEFONO = 8


def _telefono_valido(telefono):
    digitos = sum(caracter.isdigit() for caracter in telefono)
    return bool(PATRON_TELEFONO.match(telefono)) and digitos >= MINIMO_DIGITOS_TELEFONO


@dashboard_bp.before_request
@login_required
def restringir_a_colaboradores():
    """
    login_required corre primero: si no hay sesión, redirige a /login antes
    de que esta función se ejecute.

    Si hay sesión pero es de tipo "cliente", o por algún motivo no tiene
    perfil de colaborador todavía, devolvemos 403.

    Si la cuenta está baneada, la cerramos y devolvemos 403: en teoría el
    login ya lo bloquea (ver app/routes/auth.py), pero si alguien ya tenía
    una sesión abierta de antes de ser baneado, esto corta el acceso igual.
    """
    if not current_user.es_colaborador or current_user.perfil_colaborador is None:
        abort(403)
    if current_user.esta_baneado:
        logout_user()
        abort(403)


def _obtener_servicio_propio(servicio_id):
    """
    Busca un servicio y confirma que pertenezca al colaborador logueado.
    Devuelve 404 si no existe y 403 si existe pero es de otro colaborador,
    para que nadie pueda editar servicios ajenos cambiando el id en la URL.
    """
    servicio = db.session.get(Service, servicio_id)
    if servicio is None:
        abort(404)
    if not servicio.pertenece_a(current_user.perfil_colaborador):
        abort(403)
    return servicio


def _obtener_foto_portafolio_propia(foto_id):
    """Igual que _obtener_servicio_propio, pero para una foto del portafolio."""
    foto = db.session.get(PortfolioImage, foto_id)
    if foto is None:
        abort(404)
    if foto.collaborator_profile_id != current_user.perfil_colaborador.id:
        abort(403)
    return foto


def _hash_usado_por_otra_cuenta(hash_exacto, collaborator_profile_id):
    """
    True si `hash_exacto` ya existe (como foto de perfil o de portafolio)
    en una cuenta DISTINTA a `collaborator_profile_id`. Reutilizar la propia
    foto en varios lugares del propio perfil es normal y no cuenta.
    """
    en_perfiles = CollaboratorProfile.query.filter(
        CollaboratorProfile.foto_hash == hash_exacto,
        CollaboratorProfile.id != collaborator_profile_id,
    ).first()
    if en_perfiles is not None:
        return True

    en_portafolios = PortfolioImage.query.filter(
        PortfolioImage.hash_exacto == hash_exacto,
        PortfolioImage.collaborator_profile_id != collaborator_profile_id,
    ).first()
    return en_portafolios is not None


@dashboard_bp.route("/")
def index():
    """Panel principal: resumen del perfil, foto, portafolio y servicios publicados."""
    perfil = current_user.perfil_colaborador
    servicios = (
        perfil.servicios.options(joinedload(Service.categoria))
        .order_by(Service.fecha_creacion.desc())
        .all()
    )
    return render_template(
        "dashboard/panel.html",
        perfil=perfil,
        servicios=servicios,
        foto_url_actual=storage.url(perfil.foto_filename, SUBCARPETA_PERFIL) if perfil.foto_filename else None,
        cantidad_portafolio=perfil.portafolio.count(),
        cantidad_portafolio_aprobado=len(perfil.portafolio_aprobado),
        minimo_portafolio=MINIMO_FOTOS_PORTAFOLIO_PARA_PUBLICAR,
    )


@dashboard_bp.route("/perfil", methods=["GET", "POST"])
def editar_perfil():
    """Completar o actualizar los datos públicos del colaborador, incluida su foto."""
    perfil = current_user.perfil_colaborador

    if request.method == "POST":
        descripcion = request.form.get("descripcion", "").strip()
        telefono = request.form.get("telefono_whatsapp", "").strip()
        archivo_foto = request.files.get("foto")

        errores = []
        if not descripcion:
            errores.append("Contá brevemente qué servicios ofrecés.")
        if telefono and not _telefono_valido(telefono):
            errores.append(
                "El teléfono de WhatsApp tiene que tener entre 8 y 20 dígitos, "
                "con un '+' inicial opcional (ej: +503 7123 4567)."
            )
        elif len(telefono) > LONGITUD_MAXIMA_TELEFONO:
            errores.append(f"El teléfono no puede tener más de {LONGITUD_MAXIMA_TELEFONO} caracteres.")

        resultado_foto = None
        # El input de archivo es opcional en "editar": si no se seleccionó
        # nada, dejamos la foto que ya tenía. Si SÍ se seleccionó algo,
        # tiene que ser válido.
        if archivo_foto is not None and archivo_foto.filename:
            try:
                resultado_foto = procesar_imagen_subida(
                    archivo_foto,
                    SUBCARPETA_PERFIL,
                    verificar_duplicado=lambda h: _hash_usado_por_otra_cuenta(h, perfil.id),
                )
            except ImagenInvalida as error:
                errores.append(str(error))

        if errores:
            # procesar_imagen_subida ya guardó la foto nueva en disco; si el
            # resto del formulario no es válido, no se va a usar, así que se
            # borra para no dejar archivos huérfanos en static/uploads/.
            if resultado_foto is not None:
                storage.eliminar(resultado_foto["filename"], SUBCARPETA_PERFIL)
            for error in errores:
                flash(error, "error")
            return render_template(
                "dashboard/editar_perfil.html",
                perfil=perfil,
                descripcion=descripcion,
                telefono_whatsapp=telefono,
                foto_url_actual=storage.url(perfil.foto_filename, SUBCARPETA_PERFIL) if perfil.foto_filename else None,
            ), 400

        perfil.descripcion = descripcion
        perfil.telefono_whatsapp = telefono or None

        if resultado_foto is not None:
            foto_anterior = perfil.foto_filename
            perfil.foto_filename = resultado_foto["filename"]
            perfil.foto_hash = resultado_foto["hash_exacto"]
            perfil.foto_moderation_status = resultado_foto["moderation_status"]
            perfil.foto_moderation_reason = resultado_foto["moderation_reason"]
            if foto_anterior:
                storage.eliminar(foto_anterior, SUBCARPETA_PERFIL)

        db.session.commit()

        flash("Guardamos los cambios de tu perfil.", "success")
        return redirect(url_for("dashboard.index"))

    return render_template(
        "dashboard/editar_perfil.html",
        perfil=perfil,
        descripcion=perfil.descripcion or "",
        telefono_whatsapp=perfil.telefono_whatsapp or "",
        foto_url_actual=storage.url(perfil.foto_filename, SUBCARPETA_PERFIL) if perfil.foto_filename else None,
    )


@dashboard_bp.route("/portafolio")
def portafolio():
    """Panel de administración del portafolio de trabajos realizados."""
    perfil = current_user.perfil_colaborador
    fotos = perfil.portafolio.all()
    return render_template(
        "dashboard/portafolio.html",
        perfil=perfil,
        fotos=fotos,
        minimo=MINIMO_FOTOS_PORTAFOLIO_PARA_PUBLICAR,
        maximo=MAXIMO_FOTOS_PORTAFOLIO,
    )


@dashboard_bp.route("/portafolio/nueva", methods=["POST"])
def subir_foto_portafolio():
    perfil = current_user.perfil_colaborador

    if perfil.portafolio.count() >= MAXIMO_FOTOS_PORTAFOLIO:
        flash(f"Ya llegaste al máximo de {MAXIMO_FOTOS_PORTAFOLIO} fotos en tu portafolio.", "error")
        return redirect(url_for("dashboard.portafolio"))

    descripcion = request.form.get("descripcion", "").strip()
    if len(descripcion) > LONGITUD_MAXIMA_DESCRIPCION_PORTAFOLIO:
        flash(f"La descripción no puede tener más de {LONGITUD_MAXIMA_DESCRIPCION_PORTAFOLIO} caracteres.", "error")
        return redirect(url_for("dashboard.portafolio"))

    archivo = request.files.get("foto")
    try:
        resultado = procesar_imagen_subida(
            archivo,
            SUBCARPETA_PORTAFOLIO,
            verificar_duplicado=lambda h: _hash_usado_por_otra_cuenta(h, perfil.id),
        )
    except ImagenInvalida as error:
        flash(str(error), "error")
        return redirect(url_for("dashboard.portafolio"))

    foto = PortfolioImage(
        collaborator_profile_id=perfil.id,
        filename=resultado["filename"],
        descripcion=descripcion or None,
        hash_exacto=resultado["hash_exacto"],
        moderation_status=resultado["moderation_status"],
        moderation_reason=resultado["moderation_reason"],
    )
    db.session.add(foto)
    db.session.commit()

    if resultado["moderation_status"] == "flagged":
        flash("Se subió la foto, pero necesita revisión antes de hacerse pública.", "info")
    else:
        flash("Agregaste una foto a tu portafolio.", "success")
    return redirect(url_for("dashboard.portafolio"))


@dashboard_bp.route("/portafolio/<int:foto_id>/descripcion", methods=["POST"])
def actualizar_descripcion_portafolio(foto_id):
    foto = _obtener_foto_portafolio_propia(foto_id)
    descripcion = request.form.get("descripcion", "").strip()

    if len(descripcion) > LONGITUD_MAXIMA_DESCRIPCION_PORTAFOLIO:
        flash(f"La descripción no puede tener más de {LONGITUD_MAXIMA_DESCRIPCION_PORTAFOLIO} caracteres.", "error")
        return redirect(url_for("dashboard.portafolio"))

    foto.descripcion = descripcion or None
    db.session.commit()
    flash("Actualizaste la descripción.", "success")
    return redirect(url_for("dashboard.portafolio"))


@dashboard_bp.route("/portafolio/<int:foto_id>/eliminar", methods=["POST"])
def eliminar_foto_portafolio(foto_id):
    foto = _obtener_foto_portafolio_propia(foto_id)
    storage.eliminar(foto.filename, SUBCARPETA_PORTAFOLIO)
    db.session.delete(foto)
    db.session.commit()
    flash("Eliminaste la foto de tu portafolio.", "success")
    return redirect(url_for("dashboard.portafolio"))


# ----------------------------------------------------------------------
# SERVICIOS — flujo MVC de este módulo:
#   View (servicio_form.html) -> estas rutas (Controller) -> Service /
#   CollaboratorProfile (Model, app/models.py) -> resultado -> Controller
#   -> View. El Controller solo lee la petición, llama al Model, y decide
#   qué mostrar; las REGLAS (validaciones, portafolio mínimo, dueño del
#   servicio) las aplica el Model y avisa con excepciones de dominio.
# ----------------------------------------------------------------------
def _leer_formulario_servicio(form):
    """Solo lee lo que llegó en la petición; validar es trabajo del Model."""
    return {campo: form.get(campo, "").strip() for campo in CAMPOS_SERVICIO}


def _variables_formulario(datos):
    """Nombres con los que servicio_form.html vuelve a mostrar lo que la persona escribió."""
    return {
        "titulo": datos["titulo"],
        "descripcion": datos["descripcion"],
        "categoria_id": datos["categoria_id"],
        "precio_raw": datos["precio"],
        "modalidad": datos["modalidad"],
        "disponibilidad": datos["disponibilidad"],
    }


def _vista_portafolio_requerido(perfil):
    """View que explica cuántas fotos faltan antes de poder publicar un servicio."""
    faltan = MINIMO_FOTOS_PORTAFOLIO_PARA_PUBLICAR - len(perfil.portafolio_aprobado)
    return render_template(
        "dashboard/portafolio_requerido.html",
        faltan=max(faltan, 0),
        minimo=MINIMO_FOTOS_PORTAFOLIO_PARA_PUBLICAR,
    )


@dashboard_bp.route("/servicios/nuevo", methods=["GET", "POST"])
def nuevo_servicio():
    perfil = current_user.perfil_colaborador
    categorias = Category.query.order_by(Category.nombre).all()

    if request.method == "POST":
        datos = _leer_formulario_servicio(request.form)
        try:
            # Model: el colaborador publica; la regla de portafolio y las
            # validaciones de cada campo se aplican dentro de los objetos.
            servicio = perfil.publicar_servicio(datos)
        except PortafolioInsuficiente:
            return _vista_portafolio_requerido(perfil)
        except ServicioInvalido as error:
            for mensaje in error.errores:
                flash(mensaje, "error")
            return render_template(
                "dashboard/servicio_form.html",
                modo="nuevo",
                categorias=categorias,
                **_variables_formulario(datos),
            ), 400

        db.session.add(servicio)
        db.session.commit()
        flash(f'Publicaste "{servicio.titulo}".', "success")
        return redirect(url_for("dashboard.index"))

    # GET: si todavía no cumple el mínimo de portafolio, no mostramos el formulario.
    if not perfil.puede_publicar_servicio:
        return _vista_portafolio_requerido(perfil)

    return render_template(
        "dashboard/servicio_form.html",
        modo="nuevo",
        categorias=categorias,
        titulo="",
        descripcion="",
        categoria_id="",
        precio_raw="",
        modalidad="",
        disponibilidad="",
    )


@dashboard_bp.route("/servicios/<int:servicio_id>/editar", methods=["GET", "POST"])
def editar_servicio(servicio_id):
    # Editar un servicio que ya está publicado no vuelve a exigir el mínimo
    # de portafolio: esa regla es para publicar servicios nuevos, no
    # retroactiva sobre lo que ya existía.
    servicio = _obtener_servicio_propio(servicio_id)
    categorias = Category.query.order_by(Category.nombre).all()

    if request.method == "POST":
        datos = _leer_formulario_servicio(request.form)
        try:
            servicio.actualizar(datos)  # Model: valida y aplica los cambios
        except ServicioInvalido as error:
            for mensaje in error.errores:
                flash(mensaje, "error")
            return render_template(
                "dashboard/servicio_form.html",
                modo="editar",
                servicio=servicio,
                categorias=categorias,
                **_variables_formulario(datos),
            ), 400

        db.session.commit()
        flash(f'Actualizaste "{servicio.titulo}".', "success")
        return redirect(url_for("dashboard.index"))

    return render_template(
        "dashboard/servicio_form.html",
        modo="editar",
        servicio=servicio,
        categorias=categorias,
        titulo=servicio.titulo,
        descripcion=servicio.descripcion,
        categoria_id=str(servicio.category_id),
        precio_raw=str(servicio.precio),
        modalidad=servicio.modalidad,
        disponibilidad=servicio.disponibilidad,
    )
