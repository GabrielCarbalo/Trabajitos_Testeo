"""
Controller de autenticación: registro, login y logout.

Flujo MVC del REGISTRO:
  View (auth/registro.html) -> registro() [Controller] -> User.registrar()
  [Model: valida, hashea la contraseña y crea el perfil si es colaborador]
  -> el Controller guarda (commit), inicia sesión y redirige a la View.
Las REGLAS (correo válido, largo de contraseña, rol permitido, correo
duplicado) viven en la clase User (app/models.py); este archivo solo
coordina la petición y la respuesta.
"""

from urllib.parse import urlsplit

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import TIPOS_USUARIO, RegistroInvalido, User

auth_bp = Blueprint("auth", __name__)


def _es_redireccion_segura(destino):
    """
    Confirma que "next" sea una ruta interna real, no una forma disfrazada
    de mandar al usuario a otro sitio ("open redirect"). "//evil.com" o
    "/\\evil.com" parecen rutas internas a simple vista, pero el navegador
    los interpreta como "mismo esquema, host distinto" y termina saliendo
    del sitio. urlsplit().netloc detecta eso incluso cuando no hay "http://"
    explícito.
    """
    if not destino or destino.startswith("//") or destino.startswith("/\\"):
        return False
    partes = urlsplit(destino)
    return not partes.scheme and not partes.netloc and partes.path.startswith("/")


def _destino_segun_rol(usuario):
    """
    A dónde llevar a una persona cuando no pidió una página concreta: el
    administrador a su panel (se revisa primero: un admin es de tipo
    "cliente"), el colaborador al suyo y el resto al inicio.
    """
    if usuario.es_admin:
        return url_for("admin.index")
    if usuario.es_colaborador:
        return url_for("dashboard.index")
    return url_for("main.home")


CAMPOS_REGISTRO = ("nombre", "correo", "password", "tipo_usuario")


def _vista_registro(datos, estado=200):
    """View del registro. Nunca se devuelve la contraseña al formulario."""
    return render_template(
        "auth/registro.html", nombre=datos["nombre"], correo=datos["correo"], tipo_usuario=datos["tipo_usuario"]
    ), estado


@auth_bp.route("/registro", methods=["GET", "POST"])
def registro():
    # Si ya hay una sesión activa, no tiene sentido mostrar el registro de nuevo.
    if current_user.is_authenticated:
        return redirect(_destino_segun_rol(current_user))

    if request.method == "GET":
        datos = {campo: "" for campo in CAMPOS_REGISTRO}
        # Los enlaces "Ofrecer un servicio" llegan con ?tipo=colaborador para
        # dejar esa opción elegida; cualquier otro valor se ignora.
        tipo = request.args.get("tipo")
        if tipo in TIPOS_USUARIO:
            datos["tipo_usuario"] = tipo
        return _vista_registro(datos)

    # POST: el Controller solo LEE lo que llegó; validar y crear es del Model.
    datos = {campo: request.form.get(campo, "") for campo in CAMPOS_REGISTRO}
    try:
        usuario = User.registrar(datos)
        db.session.add(usuario)
        db.session.commit()
    except RegistroInvalido as error:
        for mensaje in error.errores:
            flash(mensaje, "error")
        return _vista_registro(datos, 400)
    except IntegrityError:
        # Dos registros con el mismo correo casi al mismo tiempo pueden pasar
        # la validación del Model antes de que el primero haga commit; la
        # restricción UNIQUE de la base de datos es la última defensa.
        db.session.rollback()
        flash("Ya existe una cuenta con ese correo.", "error")
        return _vista_registro(datos, 400)

    login_user(usuario)
    flash(f"¡Bienvenido/a a TRABAJITOS, {usuario.nombre}!", "success")
    return redirect(_destino_segun_rol(usuario))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(_destino_segun_rol(current_user))

    correo = ""

    if request.method == "POST":
        correo = request.form.get("correo", "").strip().lower()
        password = request.form.get("password", "")

        usuario = User.query.filter_by(correo=correo).first()

        # Mensaje genérico a propósito: no revelamos si falló el correo o la
        # contraseña, para no ayudar a alguien a "adivinar" cuentas existentes.
        if usuario is None or not usuario.check_password(password):
            flash("Correo o contraseña incorrectos.", "error")
            return render_template("auth/login.html", correo=correo), 401

        # A diferencia del error de arriba, acá SÍ decimos explícitamente
        # qué pasó: la persona ya sabe cuál es su cuenta, así que no hay
        # nada que "revelar" ocultándolo, y el pedido original pide un
        # mensaje claro (no una excusa genérica) cuando la cuenta está
        # suspendida.
        if usuario.esta_baneado:
            flash(
                "Esta cuenta fue suspendida por incumplir las normas de la plataforma.",
                "error",
            )
            return render_template("auth/login.html", correo=correo), 403

        login_user(usuario)
        flash(f"¡Hola de nuevo, {usuario.nombre}!", "success")

        # Si Flask-Login nos trajo hasta acá desde una página protegida
        # (?next=/dashboard/), volvemos ahí — pero solo si es una ruta
        # interna real (ver _es_redireccion_segura).
        siguiente = request.args.get("next")
        if _es_redireccion_segura(siguiente):
            return redirect(siguiente)
        return redirect(_destino_segun_rol(usuario))

    return render_template("auth/login.html", correo=correo)


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Cerraste sesión correctamente.", "info")
    return redirect(url_for("main.home"))
