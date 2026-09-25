"""
Modelos de datos de TRABAJITOS.

Relaciones principales:

    User (1) ---- (1) CollaboratorProfile ---- (N) Service (N) ---- (1) Category
                                    |
                                    +---- (N) PortfolioImage

Un User es la cuenta base (cliente o colaborador). Solo los usuarios de tipo
"colaborador" llegan a tener un CollaboratorProfile, que es donde vive la
información específica para ofrecer servicios (descripción, WhatsApp, foto,
portafolio, etc.). Esto evita duplicar en la tabla de usuarios datos que
solo aplican a un tipo de cuenta.

No se crea una tabla "availability" separada: para el MVP, la disponibilidad
de un servicio es un texto simple (ej. "Lunes a viernes, tardes"). Si más
adelante se necesitan horarios estructurados o calendarios, esa es la puerta
de entrada natural para una tabla propia.
"""

import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from flask_login import UserMixin
from sqlalchemy.orm import validates
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login_manager

# Valores permitidos para los campos de tipo "catálogo cerrado".
# Se validan en las rutas antes de guardar en la base de datos, y además
# quedan reforzados a nivel de base de datos con CheckConstraint más abajo.
TIPOS_USUARIO = ("cliente", "colaborador")
MODALIDADES_SERVICIO = ("hora", "dia", "tarea")

# Cuenta de acceso: "active" puede usar la plataforma con normalidad;
# "banned" no puede iniciar sesión y sus servicios/fotografías dejan de
# mostrarse públicamente (ver app/routes/auth.py y app/routes/main.py).
# El paso a "banned" es siempre una decisión de moderación manual, nunca el
# resultado directo de un detector automático (ver DESARROLLO.md).
ACCOUNT_STATUSES = ("active", "banned")

# Estados del pipeline de moderación de fotografías (perfil y portafolio):
#   pending  -> recién subida, todavía no pasó las comprobaciones
#   approved -> visible públicamente
#   flagged  -> alguna señal automática pide revisión humana; NO es pública
#   rejected -> se confirmó que incumple las reglas; NO es pública
# "flagged" y "rejected" nunca deben confundirse con una sanción a la
# cuenta: eso es un paso aparte y manual (ver ACCOUNT_STATUSES).
MODERATION_STATUSES = ("pending", "approved", "flagged", "rejected")

# Reglas de negocio del portafolio de trabajos.
MINIMO_FOTOS_PORTAFOLIO_PARA_PUBLICAR = 2
MAXIMO_FOTOS_PORTAFOLIO = 8


class DatosInvalidos(ValueError):
    """
    Excepción de dominio base: los datos recibidos incumplen alguna regla.
    Guarda TODOS los mensajes (no solo el primero) para que el Controller los
    muestre juntos en el formulario, sin tener que conocer las reglas.
    """

    def __init__(self, errores):
        super().__init__("; ".join(errores))
        self.errores = list(errores)


class ServicioInvalido(DatosInvalidos):
    """Los datos de un servicio no cumplen las reglas (módulo Servicios)."""


class RegistroInvalido(DatosInvalidos):
    """Los datos de un registro de usuario no cumplen las reglas (módulo Registro)."""


class PortafolioInsuficiente(Exception):
    """El colaborador todavía no tiene el mínimo de fotos aprobadas para publicar."""


def ahora_utc():
    """Hora actual en UTC, usada como valor por defecto en fecha_creacion."""
    return datetime.now(timezone.utc)


@login_manager.user_loader
def load_user(user_id):
    """Flask-Login usa esta función para recuperar al usuario de la sesión activa."""
    return db.session.get(User, int(user_id))


class User(UserMixin, db.Model):
    """Cuenta de acceso: puede ser un cliente o un colaborador."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    correo = db.Column(db.String(180), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    tipo_usuario = db.Column(db.String(20), nullable=False)  # "cliente" | "colaborador"
    account_status = db.Column(db.String(10), nullable=False, default="active")
    fecha_creacion = db.Column(db.DateTime, default=ahora_utc, nullable=False)

    # Relación uno-a-uno: solo existe si el usuario es colaborador.
    perfil_colaborador = db.relationship(
        "CollaboratorProfile",
        backref="usuario",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        db.CheckConstraint(
            f"tipo_usuario IN {TIPOS_USUARIO}", name="ck_users_tipo_usuario"
        ),
        db.CheckConstraint(
            f"account_status IN {ACCOUNT_STATUSES}", name="ck_users_account_status"
        ),
    )

    # ------------------------------------------------------------------
    # Reglas del dominio del registro. Viven en la clase (Model) para que
    # apliquen SIEMPRE: formulario web, seed.py o cualquier otro código.
    # ------------------------------------------------------------------
    LONGITUD_MINIMA_PASSWORD = 8
    LONGITUD_MAXIMA_NOMBRE = 120
    LONGITUD_MAXIMA_CORREO = 180
    PATRON_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    # Cada _normalizar_* recibe el valor "crudo" del formulario y devuelve el
    # valor limpio, o lanza ValueError con un mensaje para la persona.
    @classmethod
    def _normalizar_nombre(cls, valor):
        valor = (valor or "").strip()
        if not valor:
            raise ValueError("Ingresá tu nombre.")
        if len(valor) > cls.LONGITUD_MAXIMA_NOMBRE:
            raise ValueError(f"El nombre no puede tener más de {cls.LONGITUD_MAXIMA_NOMBRE} caracteres.")
        return valor

    @classmethod
    def _normalizar_correo(cls, valor):
        valor = (valor or "").strip().lower()
        if not cls.PATRON_CORREO.match(valor):
            raise ValueError("Ingresá un correo electrónico válido.")
        if len(valor) > cls.LONGITUD_MAXIMA_CORREO:
            raise ValueError(f"El correo no puede tener más de {cls.LONGITUD_MAXIMA_CORREO} caracteres.")
        return valor

    @classmethod
    def _normalizar_tipo_usuario(cls, valor):
        # Solo cliente/colaborador: el registro público nunca crea administradores.
        if valor not in TIPOS_USUARIO:
            raise ValueError("Elegí si necesitás contratar o si querés ofrecer servicios.")
        return valor

    @classmethod
    def _validar_password(cls, password):
        if len(password or "") < cls.LONGITUD_MINIMA_PASSWORD:
            raise ValueError(f"La contraseña debe tener al menos {cls.LONGITUD_MINIMA_PASSWORD} caracteres.")

    # Encapsulación: @validates corre en cada asignación (usuario.correo = ...),
    # así un User no puede quedar con correo mal formado o un rol inventado.
    @validates("nombre")
    def _validar_nombre(self, _clave, valor):
        return self._normalizar_nombre(valor)

    @validates("correo")
    def _validar_correo(self, _clave, valor):
        return self._normalizar_correo(valor)

    @validates("tipo_usuario")
    def _validar_tipo_usuario(self, _clave, valor):
        return self._normalizar_tipo_usuario(valor)

    @classmethod
    def correo_registrado(cls, correo):
        """True si ya existe una cuenta con ese correo."""
        return cls.query.filter_by(correo=correo).first() is not None

    @classmethod
    def validar_datos(cls, datos):
        """
        Valida de una vez los datos del formulario de registro. `datos` es un
        dict con: nombre, correo, password, tipo_usuario. Devuelve los valores
        limpios (sin la contraseña). Lanza RegistroInvalido con la lista
        completa de errores si algo no cumple.
        """
        limpios, errores = {}, []
        for campo, regla in (
            ("nombre", cls._normalizar_nombre),
            ("correo", cls._normalizar_correo),
        ):
            try:
                limpios[campo] = regla(datos.get(campo))
            except ValueError as error:
                errores.append(str(error))

        try:
            cls._validar_password(datos.get("password"))
        except ValueError as error:
            errores.append(str(error))

        try:
            limpios["tipo_usuario"] = cls._normalizar_tipo_usuario(datos.get("tipo_usuario"))
        except ValueError as error:
            errores.append(str(error))

        if "correo" in limpios and cls.correo_registrado(limpios["correo"]):
            errores.append("Ya existe una cuenta con ese correo.")

        if errores:
            raise RegistroInvalido(errores)
        return limpios

    @classmethod
    def registrar(cls, datos):
        """
        Crea un usuario nuevo (sin guardarlo) a partir de los datos del
        formulario: valida, guarda solo el HASH de la contraseña y, si es
        colaborador, le crea su perfil vacío (todo colaborador tiene perfil).
        Guardar en la base de datos (commit) es responsabilidad del Controller.
        """
        usuario = cls(**cls.validar_datos(datos))
        usuario.set_password(datos["password"])
        if usuario.es_colaborador:
            usuario.perfil_colaborador = CollaboratorProfile()
        return usuario

    def set_password(self, password):
        """Guarda un hash seguro de la contraseña, nunca el texto plano."""
        self._validar_password(password)
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Compara una contraseña en texto plano contra el hash almacenado."""
        return check_password_hash(self.password_hash, password)

    @property
    def es_colaborador(self):
        return self.tipo_usuario == "colaborador"

    @property
    def esta_baneado(self):
        return self.account_status == "banned"

    def __repr__(self):
        return f"<User {self.correo}>"


class CollaboratorProfile(db.Model):
    """
    Datos específicos de un colaborador: lo que se muestra en su perfil público.

    Nota: cuando el resto del código habla de "colaborador_id" (por ejemplo
    en la ruta /colaborador/<colaborador_id> o en Service.collaborator_profile_id)
    siempre se refiere al id de ESTA tabla (CollaboratorProfile.id), nunca al
    id de User. Un colaborador se identifica públicamente por su perfil, no
    por su cuenta de acceso.
    """

    __tablename__ = "collaborator_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)

    descripcion = db.Column(db.Text, nullable=True)
    telefono_whatsapp = db.Column(db.String(20), nullable=True)

    # Foto de perfil: guardamos solo el nombre del archivo generado (UUID),
    # nunca una URL externa ni el nombre original del archivo subido (ver
    # app/services/image_storage.py). foto_hash es el SHA-256 del contenido,
    # usado para detectar si dos cuentas distintas suben la misma imagen.
    foto_filename = db.Column(db.String(255), nullable=True)
    foto_hash = db.Column(db.String(64), nullable=True, index=True)
    foto_moderation_status = db.Column(db.String(10), nullable=False, default="approved")
    foto_moderation_reason = db.Column(db.String(255), nullable=True)

    servicios = db.relationship(
        "Service", backref="colaborador", cascade="all, delete-orphan", lazy="dynamic"
    )
    portafolio = db.relationship(
        "PortfolioImage",
        backref="perfil",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="PortfolioImage.fecha_subida.desc()",
    )

    __table_args__ = (
        db.CheckConstraint(
            f"foto_moderation_status IN {MODERATION_STATUSES}",
            name="ck_collaborator_profiles_foto_moderation_status",
        ),
    )

    @property
    def foto_visible(self):
        """True si hay foto de perfil Y ya pasó moderación (se puede mostrar públicamente)."""
        return bool(self.foto_filename) and self.foto_moderation_status == "approved"

    @property
    def portafolio_aprobado(self):
        """Fotos de portafolio que ya se pueden mostrar públicamente."""
        return self.portafolio.filter_by(moderation_status="approved").all()

    @property
    def puede_publicar_servicio(self):
        """
        Regla de confianza: se necesitan al menos MINIMO_FOTOS_PORTAFOLIO_PARA_PUBLICAR
        fotos de trabajos ya aprobadas antes de poder publicar un nuevo servicio
        (ver app/routes/dashboard.py: nuevo_servicio).
        """
        return len(self.portafolio_aprobado) >= MINIMO_FOTOS_PORTAFOLIO_PARA_PUBLICAR

    def publicar_servicio(self, datos):
        """
        El colaborador publica un servicio nuevo. Aplica la regla de confianza
        (mínimo de portafolio) y delega la validación de los campos a Service.
        Devuelve el objeto Service ya validado; guardarlo en la base de datos
        (commit) es responsabilidad del Controller.

        Lanza PortafolioInsuficiente o ServicioInvalido si no se puede publicar.
        """
        if not self.puede_publicar_servicio:
            raise PortafolioInsuficiente()
        return Service.desde_datos(self.id, datos)

    def __repr__(self):
        return f"<CollaboratorProfile user_id={self.user_id}>"


class PortfolioImage(db.Model):
    """Una fotografía de un trabajo realizado, publicada por un colaborador."""

    __tablename__ = "portfolio_images"

    id = db.Column(db.Integer, primary_key=True)
    collaborator_profile_id = db.Column(
        db.Integer, db.ForeignKey("collaborator_profiles.id"), nullable=False, index=True
    )

    filename = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.String(200), nullable=True)
    fecha_subida = db.Column(db.DateTime, default=ahora_utc, nullable=False)

    moderation_status = db.Column(db.String(10), nullable=False, default="pending")
    moderation_reason = db.Column(db.String(255), nullable=True)

    # SHA-256 del contenido exacto (detecta duplicados idénticos entre
    # cuentas distintas). hash_perceptual queda preparado para cuando se
    # apruebe una librería de hashing perceptual (ver image_quality_service.py
    # y el reporte de dependencias propuestas) — hoy siempre es NULL.
    hash_exacto = db.Column(db.String(64), nullable=False, index=True)
    hash_perceptual = db.Column(db.String(64), nullable=True)

    __table_args__ = (
        db.CheckConstraint(
            f"moderation_status IN {MODERATION_STATUSES}",
            name="ck_portfolio_images_moderation_status",
        ),
    )

    def __repr__(self):
        return f"<PortfolioImage {self.filename}>"


class Category(db.Model):
    """Categoría de servicio (Limpieza, Jardinería, Mascotas, etc.)."""

    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(60), unique=True, nullable=False)
    slug = db.Column(db.String(60), unique=True, nullable=False)

    servicios = db.relationship("Service", backref="categoria", lazy="dynamic")

    def __repr__(self):
        return f"<Category {self.nombre}>"


class Service(db.Model):
    """Un servicio publicado por un colaborador."""

    __tablename__ = "services"

    id = db.Column(db.Integer, primary_key=True)
    # index=True en ambas foreign keys: son las columnas por las que se va
    # a filtrar en /explorar (Fase 6), conviene tenerlas indexadas desde ya.
    collaborator_profile_id = db.Column(
        db.Integer, db.ForeignKey("collaborator_profiles.id"), nullable=False, index=True
    )
    category_id = db.Column(
        db.Integer, db.ForeignKey("categories.id"), nullable=False, index=True
    )

    titulo = db.Column(db.String(120), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    precio = db.Column(db.Numeric(8, 2), nullable=False)
    modalidad = db.Column(db.String(10), nullable=False)  # "hora" | "dia" | "tarea"
    disponibilidad = db.Column(db.String(160), nullable=False)
    activo = db.Column(db.Boolean, default=True, nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=ahora_utc, nullable=False)

    __table_args__ = (
        db.CheckConstraint(
            f"modalidad IN {MODALIDADES_SERVICIO}", name="ck_services_modalidad"
        ),
    )

    # ------------------------------------------------------------------
    # Reglas del dominio. Viven en la clase (Model) y no en las rutas
    # (Controller) para que apliquen SIEMPRE, se cree el servicio desde
    # el formulario, desde seed.py o desde cualquier otro lugar.
    # ------------------------------------------------------------------
    LONGITUD_MAXIMA_TITULO = 120
    LONGITUD_MAXIMA_DISPONIBILIDAD = 160
    PRECIO_MAXIMO = Decimal("999999.99")

    _MODALIDADES_LEGIBLES = {"hora": "hora", "dia": "día", "tarea": "tarea"}

    @property
    def modalidad_legible(self):
        """Texto para mostrar ('día' en vez de 'dia'), usado en todas las tarjetas de servicio."""
        return self._MODALIDADES_LEGIBLES[self.modalidad]

    # Cada método _normalizar_* recibe el valor "crudo" (tal como llega de un
    # formulario) y devuelve el valor limpio, o lanza ValueError con un mensaje
    # pensado para la persona. Son la única fuente de verdad de cada regla.
    @classmethod
    def _normalizar_titulo(cls, valor):
        valor = (valor or "").strip()
        if not valor:
            raise ValueError("Ponele un título a tu servicio.")
        if len(valor) > cls.LONGITUD_MAXIMA_TITULO:
            raise ValueError(f"El título no puede tener más de {cls.LONGITUD_MAXIMA_TITULO} caracteres.")
        return valor

    @classmethod
    def _normalizar_descripcion(cls, valor):
        valor = (valor or "").strip()
        if not valor:
            raise ValueError("Agregá una descripción breve.")
        return valor

    @classmethod
    def _normalizar_modalidad(cls, valor):
        if valor not in MODALIDADES_SERVICIO:
            raise ValueError("Elegí una modalidad de cobro válida.")
        return valor

    @classmethod
    def _normalizar_disponibilidad(cls, valor):
        valor = (valor or "").strip()
        if not valor:
            raise ValueError('Indicá tu disponibilidad (por ejemplo: "Lunes a viernes, tardes").')
        if len(valor) > cls.LONGITUD_MAXIMA_DISPONIBILIDAD:
            raise ValueError(
                f"La disponibilidad no puede tener más de {cls.LONGITUD_MAXIMA_DISPONIBILIDAD} caracteres."
            )
        return valor

    @classmethod
    def _normalizar_precio(cls, valor):
        # Decimal("nan") y Decimal("inf") se crean sin error, por eso además de
        # capturar InvalidOperation hay que confirmar que el número sea finito.
        mensaje = "Ingresá un precio referencial válido (solo números)."
        try:
            precio = Decimal(str(valor).strip())
        except InvalidOperation:
            raise ValueError(mensaje)
        if not precio.is_finite():
            raise ValueError(mensaje)
        if precio <= 0:
            raise ValueError("El precio tiene que ser mayor a 0.")
        if precio > cls.PRECIO_MAXIMO:
            raise ValueError(f"El precio no puede ser mayor a ${cls.PRECIO_MAXIMO:,.2f}.")
        return precio.quantize(Decimal("0.01"))

    # Encapsulación: @validates se ejecuta cada vez que se ASIGNA el atributo
    # (servicio.precio = ...), así que un objeto Service no puede llegar a
    # tener un título vacío o un precio negativo por ningún camino.
    @validates("titulo")
    def _validar_titulo(self, _clave, valor):
        return self._normalizar_titulo(valor)

    @validates("descripcion")
    def _validar_descripcion(self, _clave, valor):
        return self._normalizar_descripcion(valor)

    @validates("modalidad")
    def _validar_modalidad(self, _clave, valor):
        return self._normalizar_modalidad(valor)

    @validates("disponibilidad")
    def _validar_disponibilidad(self, _clave, valor):
        return self._normalizar_disponibilidad(valor)

    @validates("precio")
    def _validar_precio(self, _clave, valor):
        return self._normalizar_precio(valor)

    @classmethod
    def validar_datos(cls, datos):
        """
        Valida de una vez todos los campos del formulario de servicio.
        `datos` es un dict con: titulo, descripcion, categoria_id, modalidad,
        precio, disponibilidad (todos como texto). Devuelve el dict con los
        valores ya limpios (y la Category encontrada). Lanza ServicioInvalido
        con la lista completa de errores si algo no cumple.
        """
        limpios, errores = {}, []

        reglas = (
            ("titulo", cls._normalizar_titulo),
            ("descripcion", cls._normalizar_descripcion),
            ("modalidad", cls._normalizar_modalidad),
            ("precio", cls._normalizar_precio),
            ("disponibilidad", cls._normalizar_disponibilidad),
        )
        for campo, regla in reglas:
            try:
                limpios[campo] = regla(datos.get(campo))
            except ValueError as error:
                errores.append(str(error))

        # Solo dígitos ASCII y de largo acotado: isdigit() acepta cosas como
        # "²" que int() no convierte, y un número enorme no entra en un
        # INTEGER de la base — los dos casos terminaban en un error 500.
        categoria_id = str(datos.get("categoria_id") or "").strip()
        categoria = (
            db.session.get(Category, int(categoria_id))
            if re.fullmatch(r"[0-9]{1,9}", categoria_id)
            else None
        )
        if categoria is None:
            errores.append("Elegí una categoría." if not categoria_id else "La categoría elegida no es válida.")
        else:
            limpios["category_id"] = categoria.id

        if errores:
            raise ServicioInvalido(errores)
        return limpios

    @classmethod
    def desde_datos(cls, collaborator_profile_id, datos):
        """Construye un Service nuevo (sin guardarlo) a partir de datos de formulario."""
        return cls(collaborator_profile_id=collaborator_profile_id, **cls.validar_datos(datos))

    def actualizar(self, datos):
        """Aplica cambios de un formulario a este servicio, con las mismas reglas que al crearlo."""
        for campo, valor in self.validar_datos(datos).items():
            setattr(self, campo, valor)

    def pertenece_a(self, perfil):
        """Regla de autorización del dominio: un servicio solo lo administra su dueño."""
        return perfil is not None and self.collaborator_profile_id == perfil.id

    def __repr__(self):
        return f"<Service {self.titulo}>"
