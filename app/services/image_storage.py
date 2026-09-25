"""
Almacenamiento de imágenes subidas por los usuarios (foto de perfil y
portafolio de trabajos).

Se define una interfaz simple (ImageStorage) para que, cuando TRABAJITOS
salga a producción, alcance con escribir una CloudImageStorage (por ejemplo
para Cloudinary o S3) que implemente los mismos tres métodos, sin tocar las
rutas que ya usan `storage.guardar(...)`, `storage.eliminar(...)` y
`storage.url(...)`. Por ahora solo existe LocalImageStorage, que guarda los
archivos dentro de app/static/uploads/.

Los archivos NUNCA se guardan con su nombre original: cada uno recibe un
nombre generado con uuid4, tanto por seguridad (evita path traversal y
colisiones) como para no filtrar el nombre del archivo tal como estaba en
el dispositivo de la persona.
"""

import os
import uuid
from abc import ABC, abstractmethod

from flask import current_app, url_for


class ImageStorage(ABC):
    """Interfaz que cualquier backend de almacenamiento de imágenes debe cumplir."""

    @abstractmethod
    def guardar(self, contenido: bytes, extension: str, subcarpeta: str) -> str:
        """Guarda los bytes de la imagen y devuelve el nombre de archivo generado."""

    @abstractmethod
    def eliminar(self, filename: str, subcarpeta: str) -> None:
        """Borra una imagen previamente guardada (no falla si ya no existe)."""

    @abstractmethod
    def url(self, filename: str, subcarpeta: str) -> str:
        """URL pública para mostrar la imagen en una plantilla."""


class LocalImageStorage(ImageStorage):
    """Guarda las imágenes en el disco local, dentro de app/static/uploads/<subcarpeta>/."""

    def _carpeta(self, subcarpeta: str) -> str:
        carpeta = os.path.join(current_app.static_folder, "uploads", subcarpeta)
        os.makedirs(carpeta, exist_ok=True)
        return carpeta

    def guardar(self, contenido: bytes, extension: str, subcarpeta: str) -> str:
        nombre = f"{uuid.uuid4().hex}.{extension}"
        ruta = os.path.join(self._carpeta(subcarpeta), nombre)
        with open(ruta, "wb") as archivo:
            archivo.write(contenido)
        return nombre

    def eliminar(self, filename: str, subcarpeta: str) -> None:
        if not filename:
            return
        ruta = os.path.join(current_app.static_folder, "uploads", subcarpeta, filename)
        if os.path.isfile(ruta):
            os.remove(ruta)

    def url(self, filename: str, subcarpeta: str) -> str:
        return url_for("static", filename=f"uploads/{subcarpeta}/{filename}")


# Instancia única que usan las rutas. El día que se agregue CloudImageStorage,
# este es el único lugar que hay que cambiar.
storage: ImageStorage = LocalImageStorage()
