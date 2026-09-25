"""
Rutas públicas principales: Home, Explorar (listado + búsqueda + filtros) y
el perfil público de un colaborador con su botón de contacto por WhatsApp.
"""

import math
import re

from flask import Blueprint, abort, render_template, request
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from app import db
from app.models import MODALIDADES_SERVICIO, Category, CollaboratorProfile, Service, User

main_bp = Blueprint("main", __name__)


def _link_whatsapp(telefono):
    """
    Convierte un teléfono guardado (ej. "+503 7123 4567") en un link de
    WhatsApp válido (ej. "https://wa.me/50371234567"). wa.me solo acepta
    dígitos, sin "+", espacios ni guiones.
    """
    if not telefono:
        return None
    solo_digitos = re.sub(r"\D", "", telefono)
    if not solo_digitos:
        return None
    return f"https://wa.me/{solo_digitos}"


def _escapar_like(texto):
    """
    Escapa los comodines de LIKE/ILIKE ("%" y "_") para que una búsqueda
    como "50% descuento" busque ese texto literal en vez de comportarse
    como un patrón. No es una defensa de seguridad (la consulta ya va
    parametrizada, sin riesgo de inyección) — es para que los resultados no
    sean raros cuando alguien busca un texto que casualmente tiene "%" o "_".
    """
    return texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


@main_bp.route("/")
def home():
    """Página de inicio: categorías y servicios destacados desde la base de datos."""
    categorias = Category.query.order_by(Category.nombre).all()

    # "Servicios disponibles": los más recientes primero, limitados a 6 para
    # que la sección se sienta curada y no como un listado infinito.
    # joinedload trae categoría y colaborador (+ su usuario) en la misma
    # consulta: cada tarjeta necesita ambos, así evitamos una query por
    # tarjeta (problema N+1).
    servicios_destacados = (
        Service.query.filter_by(activo=True)
        .join(CollaboratorProfile)
        .join(User)
        .filter(User.account_status == "active")
        .options(
            joinedload(Service.categoria),
            joinedload(Service.colaborador).joinedload(CollaboratorProfile.usuario),
        )
        .order_by(Service.fecha_creacion.desc())
        .limit(6)
        .all()
    )

    return render_template(
        "index.html", categorias=categorias, servicios=servicios_destacados
    )


@main_bp.route("/explorar")
def explorar():
    """
    Listado de servicios con búsqueda de texto libre y filtros por
    categoría, modalidad y precio máximo. Todos los filtros son opcionales
    y se combinan entre sí (AND), y viajan por querystring (GET) para que
    la búsqueda se pueda compartir/recargar con el mismo resultado.
    """
    categorias = Category.query.order_by(Category.nombre).all()

    q = request.args.get("q", "").strip()
    categoria_slug = request.args.get("categoria", "").strip()
    modalidad = request.args.get("modalidad", "").strip()
    precio_max_raw = request.args.get("precio_max", "").strip()

    # join a CollaboratorProfile/User + filtro de account_status: los
    # servicios de una cuenta baneada dejan de mostrarse públicamente (ver
    # Parte 11 del pedido de fotografías/moderación) sin necesidad de
    # borrarlos ni de tocar Service.activo, que sigue significando otra cosa.
    consulta = (
        Service.query.filter_by(activo=True)
        .join(CollaboratorProfile)
        .join(User)
        .filter(User.account_status == "active")
        .options(
            joinedload(Service.categoria),
            joinedload(Service.colaborador).joinedload(CollaboratorProfile.usuario),
        )
    )

    if q:
        patron = f"%{_escapar_like(q)}%"
        consulta = consulta.filter(
            or_(
                Service.titulo.ilike(patron, escape="\\"),
                Service.descripcion.ilike(patron, escape="\\"),
            )
        )

    if categoria_slug:
        consulta = consulta.join(Category).filter(Category.slug == categoria_slug)

    if modalidad in MODALIDADES_SERVICIO:
        consulta = consulta.filter(Service.modalidad == modalidad)

    if precio_max_raw:
        try:
            precio_max = float(precio_max_raw)
            if math.isfinite(precio_max):
                consulta = consulta.filter(Service.precio <= precio_max)
        except ValueError:
            # Un valor no numérico en el filtro de precio se ignora en vez
            # de romper la búsqueda: mejor mostrar todo que dar un error 500.
            pass

    servicios = consulta.order_by(Service.fecha_creacion.desc()).all()

    return render_template(
        "explorar.html",
        categorias=categorias,
        servicios=servicios,
        q=q,
        categoria_slug=categoria_slug,
        modalidad=modalidad,
        precio_max_raw=precio_max_raw,
    )


@main_bp.route("/colaborador/<int:colaborador_id>")
def perfil_colaborador(colaborador_id):
    """Perfil público de un colaborador: foto, descripción, portafolio, servicios y WhatsApp."""
    perfil = db.session.get(CollaboratorProfile, colaborador_id)
    if perfil is None:
        abort(404)

    # Una cuenta baneada no debe seguir mostrando su perfil con normalidad
    # (ver Parte 11): en vez de servicios y fotos, la página explica que la
    # cuenta fue suspendida. No usamos 404 porque el perfil sí existe — la
    # razón por la que no se muestra es otra y conviene decirla con claridad.
    if perfil.usuario.esta_baneado:
        return render_template("perfil_colaborador.html", perfil=perfil, baneado=True)

    servicios = (
        perfil.servicios.filter_by(activo=True)
        .options(joinedload(Service.categoria))
        .order_by(Service.fecha_creacion.desc())
        .all()
    )

    return render_template(
        "perfil_colaborador.html",
        perfil=perfil,
        baneado=False,
        servicios=servicios,
        portafolio=perfil.portafolio_aprobado,
        whatsapp_link=_link_whatsapp(perfil.telefono_whatsapp),
    )
