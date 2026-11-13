"""
Cuenta personal: cada persona (cliente, colaborador o administrador) ve sus
datos y puede cambiar su nombre y su contraseña.

Ninguna ruta lleva un id: siempre se trabaja sobre current_user, así nadie
puede ver ni modificar la cuenta de otra persona cambiando una URL. El correo
es de solo lectura (es la credencial de acceso). Las REGLAS (largo del nombre,
contraseña actual correcta, mínimo de la nueva) viven en User (app/models.py).
"""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.models import CuentaInvalida

cuenta_bp = Blueprint("cuenta", __name__, url_prefix="/cuenta")


@cuenta_bp.before_request
@login_required
def requerir_sesion():
    """Toda la sección es privada: sin sesión, login_required redirige a /login."""


def _vista(nombre, estado=200):
    """View de la cuenta. Nunca se devuelven contraseñas al formulario."""
    return render_template("cuenta/index.html", nombre=nombre), estado


@cuenta_bp.route("/")
def index():
    return _vista(current_user.nombre)


@cuenta_bp.route("/nombre", methods=["POST"])
def actualizar_nombre():
    nombre = request.form.get("nombre", "")
    try:
        current_user.actualizar_nombre(nombre)
    except CuentaInvalida as error:
        for mensaje in error.errores:
            flash(mensaje, "error")
        return _vista(nombre, 400)

    db.session.commit()
    flash("Actualizamos tu nombre.", "success")
    return redirect(url_for("cuenta.index"))


@cuenta_bp.route("/password", methods=["POST"])
def cambiar_password():
    try:
        current_user.cambiar_password(
            request.form.get("password_actual", ""),
            request.form.get("password_nueva", ""),
            request.form.get("password_confirmacion", ""),
        )
    except CuentaInvalida as error:
        for mensaje in error.errores:
            flash(mensaje, "error")
        return _vista(current_user.nombre, 400)

    db.session.commit()
    flash("Cambiaste tu contraseña.", "success")
    return redirect(url_for("cuenta.index"))
