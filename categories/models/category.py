# categories/models/category.py
from django.db import models
from django.core.exceptions import ValidationError

class Category(models.Model):
    """
    Modelo de categoría.

    Objetivo:
    - Representar una categoría simple y estable para el dominio de GoPadel.
    - Mantener el contrato mínimo que ya usa el front (name, is_active).
    - Preparar validaciones a nivel de dominio sin forzar cambios en otras capas.
    """

    # Guardo el nombre tal cual lo necesita la UI. No fuerzo unicidad acá
    # porque prefiero controlarlo con un UniqueConstraint a nivel Meta (DB).
    name = models.CharField(max_length=20, unique=False)

    # Flag de activación para permitir filtrar y ocultar sin borrar.
    is_active = models.BooleanField(default=True)

    class Meta:
        # Mantengo una tabla clara en plural (coherente con MySQL).
        db_table = "categories"

        # Nombres legibles para admin o futuras herramientas.
        verbose_name = "Category"
        verbose_name_plural = "Categories"

        # Nombre de relación por defecto si otra entidad referencia Category (FK).
        default_related_name = "categories"

        # Defino un orden por defecto **coherente** con el repositorio
        # (el repo usa order_by("id") como base). Esto evita resultados distintos
        # si alguien consulta el modelo sin pasar por el repo.
        ordering = ["id"]

        # Índices útiles para filtros frecuentes.
        indexes = [
            models.Index(fields=["is_active"], name="cat_is_active_idx"),
            models.Index(fields=["name"],      name="cat_name_idx"),
        ]

        # Unicidad por nombre. En MySQL con collation *_ci (case-insensitive) ya
        # se comporta de manera insensible a mayúsculas/minúsculas. Si tu base
        # usa otra collation, conviene ajustar el campo con db_collation.
        constraints = [
            models.UniqueConstraint(fields=["name"], name="uq_category_name"),
        ]
        # Si tu esquema usa collation distinta y necesitás garantizar case-insensitive por campo:
        # name = models.CharField(..., db_collation="utf8mb4_unicode_ci")

    def clean(self):
        """
        Normalizo y valido antes de guardar cuando se invoque full_clean() desde el service.

        Decisiones:
        - Trimeo espacios para evitar duplicados por diferencias triviales ("  Pro  " vs "Pro").
        - Evito nombres vacíos después de trim (error de usuario).
        """
        # Normalizo espacios en el nombre
        self.name = (self.name or "").strip()

        # Valido que el nombre no quede vacío después de normalizar
        if not self.name:
            raise ValidationError({"name": ["El nombre no puede estar vacío."]})

    def __str__(self):
        # Devuelvo el nombre para que aparezca legible en admin y logs
        return self.name
