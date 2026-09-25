"""
Validación y orquestación de subida de imágenes (foto de perfil y
portafolio). Junta image_storage (dónde se guarda el archivo) con
image_quality_service (qué señales se evalúan) para que las rutas de
app/routes/dashboard.py no repitan esta lógica entre ambos casos de uso.
"""

from app.services import image_quality_service
from app.services.image_storage import storage

# 5 MB — límite pedido para la foto de perfil; se reutiliza también para
# cada foto del portafolio por consistencia (mismo tipo de archivo).
TAMANO_MAXIMO_BYTES = 5 * 1024 * 1024

EXTENSIONES_PERMITIDAS_TEXTO = "JPG, PNG o WEBP"

SUBCARPETA_PERFIL = "profile"
SUBCARPETA_PORTAFOLIO = "portfolio"


class ImagenInvalida(Exception):
    """
    Error con un mensaje ya listo para mostrarle a la persona que subió la
    imagen. Siempre describe un hecho verificable (tipo de archivo, tamaño),
    nunca una acusación — eso es justamente lo que pide la Parte 24 del
    pedido: explicar el motivo sin sonar acusatorio.
    """


def _detectar_formato_real(cabecera: bytes):
    """
    Confirma el formato real de la imagen mirando sus primeros bytes
    ("magic numbers"), en vez de confiar en la extensión del archivo o en
    el Content-Type que mandó el navegador (los dos se pueden falsear
    fácilmente cambiando el nombre del archivo). No necesita ninguna
    librería: los tres formatos permitidos se reconocen con una firma de
    bytes fija y documentada públicamente.

    Devuelve la extensión a usar para el archivo guardado, o None si no es
    ninguno de los formatos permitidos.
    """
    if cabecera[:3] == b"\xff\xd8\xff":
        return "jpg"
    if cabecera[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if cabecera[:4] == b"RIFF" and cabecera[8:12] == b"WEBP":
        return "webp"
    return None


def procesar_imagen_subida(file_storage, subcarpeta, verificar_duplicado):
    """
    Valida, guarda y evalúa una imagen subida por un colaborador.

    `verificar_duplicado` es un callable que recibe el hash exacto ya
    calculado y devuelve True si esa imagen ya existe en OTRA cuenta. La
    foto de perfil se compara contra CollaboratorProfile.foto_hash y el
    portafolio contra PortfolioImage.hash_exacto — cada caso arma su propia
    consulta, por eso esta función recibe la comparación como parámetro en
    vez de tener esa lógica acá adentro.

    Devuelve un dict con filename / hash_exacto / moderation_status /
    moderation_reason. Lanza ImagenInvalida si el archivo no es válido —
    en ese caso no se guarda nada.
    """
    if file_storage is None or not file_storage.filename:
        raise ImagenInvalida("No se recibió ninguna imagen.")

    contenido = file_storage.read()

    if len(contenido) == 0:
        raise ImagenInvalida("El archivo llegó vacío. Probá seleccionarlo de nuevo.")

    if len(contenido) > TAMANO_MAXIMO_BYTES:
        raise ImagenInvalida(
            f"La imagen pesa demasiado (máximo {TAMANO_MAXIMO_BYTES // (1024 * 1024)} MB)."
        )

    extension = _detectar_formato_real(contenido[:16])
    if extension is None:
        raise ImagenInvalida(
            "Esta fotografía no puede publicarse porque el tipo de archivo no es "
            f"compatible. Subí una imagen en formato {EXTENSIONES_PERMITIDAS_TEXTO}."
        )

    hash_exacto = image_quality_service.calcular_hash_exacto(contenido)
    duplicado = verificar_duplicado(hash_exacto)
    moderation_status, moderation_reason = image_quality_service.evaluar_imagen(contenido, duplicado)

    filename = storage.guardar(contenido, extension, subcarpeta)

    return {
        "filename": filename,
        "hash_exacto": hash_exacto,
        "moderation_status": moderation_status,
        "moderation_reason": moderation_reason,
    }
