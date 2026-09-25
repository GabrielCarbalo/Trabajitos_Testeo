"""
image_quality_service — capa de señales de calidad/confianza para las
fotografías que suben los colaboradores (perfil y portafolio).

IMPORTANTE — qué hace esto hoy y qué NO hace todavía:

  Implementado ahora mismo (sin dependencias nuevas, solo librería estándar
  de Python):
    - Hash exacto (SHA-256) de cada imagen, para detectar si dos cuentas
      distintas suben literalmente el mismo archivo.

  Preparado pero INACTIVO — necesita que se apruebe una librería nueva
  antes de activarse (ver el reporte final de la sesión y
  DESARROLLO.md, sección "Dependencias propuestas, pendientes de
  aprobación"):
    - Hash perceptual (detectar imágenes "casi idénticas", no solo
      idénticas byte a byte). Requeriría la librería `imagehash`.
    - Detección de contenido NSFW/sexual. Requeriría un modelo de
      clasificación de imágenes.
    - Detección de imágenes generadas por IA. Es, de las tres, la más
      inmadura: hoy no existe un detector confiable a nivel general y
      cualquier resultado sería más ruido que señal.

  NUNCA implementado como una verdad absoluta: ningún resultado de esta
  capa "sentencia" una imagen. Como mucho, decide si el estado inicial de
  moderación es "approved" o "flagged" (ver evaluar_imagen). Pasar a
  "rejected" o banear una cuenta es siempre una decisión humana posterior
  (ver ACCOUNT_STATUSES y MODERATION_STATUSES en app/models.py).
"""

import hashlib

# Flags de activación: hoy en False porque no hay ninguna librería instalada
# para estos chequeos todavía. Cuando se apruebe e instale una, el trabajo
# es implementar la función correspondiente de este archivo y cambiar el
# flag — el resto del código (rutas, plantillas) ya está preparado para
# leer un resultado real en vez de None.
AI_IMAGE_CHECK = False
NSFW_CHECK = False
PERCEPTUAL_HASH_CHECK = False


def calcular_hash_exacto(contenido: bytes) -> str:
    """SHA-256 del contenido del archivo, en hexadecimal."""
    return hashlib.sha256(contenido).hexdigest()


def calcular_hash_perceptual(contenido: bytes):
    """
    Hash perceptual (detectaría imágenes recortadas/comprimidas/re-escaladas
    a partir de la misma foto original, no solo copias exactas).

    Pendiente de activar: requiere la librería `imagehash` (ver reporte de
    dependencias propuestas). Devuelve None mientras tanto.
    """
    if not PERCEPTUAL_HASH_CHECK:
        return None
    raise NotImplementedError("Falta instalar y aprobar la librería de hashing perceptual.")


def evaluar_nsfw(contenido: bytes):
    """
    Probabilidad (0.0–1.0) de que la imagen contenga contenido sexual/NSFW.

    Pendiente de activar: requiere aprobar e instalar un modelo de
    clasificación (ver reporte de dependencias propuestas). Devuelve None
    mientras tanto — None significa "no evaluado", nunca "aprobado".
    """
    if not NSFW_CHECK:
        return None
    raise NotImplementedError("Falta instalar y aprobar un detector de contenido NSFW.")


def evaluar_ai_generada(contenido: bytes):
    """
    Probabilidad (0.0–1.0) de que la imagen esté generada por IA.

    Pendiente de activar. A diferencia de los otros dos chequeos, hoy no
    hay una opción local madura y confiable para esto (ver reporte final).
    Devuelve None mientras tanto.
    """
    if not AI_IMAGE_CHECK:
        return None
    raise NotImplementedError("Falta instalar y aprobar un detector de imágenes generadas por IA.")


def evaluar_imagen(contenido: bytes, hay_duplicado_de_otra_cuenta: bool):
    """
    Decide el estado inicial de moderación de una imagen recién subida,
    combinando las señales que SÍ tenemos disponibles hoy.

    - Si el hash exacto coincide con una imagen de OTRA cuenta: "flagged"
      (requiere revisión humana), con un motivo claro y no acusatorio.
    - Si no hay ninguna señal de alerta: "approved". Esto es honesto dado
      el estado actual del proyecto: no hay todavía un detector NSFW ni de
      IA activo (ver AI_IMAGE_CHECK / NSFW_CHECK arriba), así que no
      podemos justificar dejar todo en "pending" indefinidamente sin un
      proceso de revisión manual real detrás. Documentado en DESARROLLO.md.

    Devuelve (moderation_status, moderation_reason).
    """
    if hay_duplicado_de_otra_cuenta:
        return "flagged", (
            "Esta fotografía coincide exactamente con una ya publicada por otra cuenta. "
            "Queda en revisión antes de mostrarse públicamente."
        )

    return "approved", None
