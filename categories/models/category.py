# categories/models/category.py
from django.db import models
from django.core.exceptions import ValidationError

class Category(models.Model):
    """
    Modelo de categoría.

    Yo mantengo el contrato mínimo que usa la UI (name, is_active) y
    las validaciones de dominio básicas (strip + no vacío).
    """

    # Alineo la longitud con los serializers (255) para no limitar nombres reales.
    name = models.CharField(max_length=20, unique=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "categories"
        verbose_name = "Category"
        verbose_name_plural = "Categories"

        # Yo dejo un related_name por defecto coherente si otras FK apuntan acá.
        default_related_name = "categories"

        # Mantengo el mismo orden que uso en el repositorio para evitar sorpresas.
        ordering = ["id"]

        indexes = [
            models.Index(fields=["is_active"], name="cat_is_active_idx"),
            models.Index(fields=["name"],      name="cat_name_idx"),
        ]

        # Unicidad por nombre en DB. Si la collation de la DB es *_ci, ya es case-insensitive.
        constraints = [
            models.UniqueConstraint(fields=["name"], name="uq_category_name"),
        ]
        # Si necesito case-insensitive por campo y la DB no lo da:
        # name = models.CharField(..., db_collation="utf8mb4_unicode_ci")

    def clean(self):
        """
        Yo normalizo y valido antes de guardar cuando se invoque full_clean().
        """
        self.name = (self.name or "").strip()
        if not self.name:
            raise ValidationError({"name": ["El nombre no puede estar vacío."]})

    def __str__(self):
        return self.name
