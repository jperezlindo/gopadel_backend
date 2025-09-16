# categories/models/category.py
from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=20, unique=False)  # unicidad vía constraint abajo
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "categories"                 # nombre claro en plural (MySQL)
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        default_related_name = "categories"
        ordering = ["name"]                     # orden alfabético por defecto
        indexes = [
            models.Index(fields=["is_active"], name="cat_is_active_idx"),
            models.Index(fields=["name"],      name="cat_name_idx"),
        ]
        constraints = [
            # En MySQL con *_ci ya es case-insensitive:
            models.UniqueConstraint(fields=["name"], name="uq_category_name"),
        ]
        # Si en tu DB usás otra collation por app/schema, podés forzar por campo así:
        # name = models.CharField(..., db_collation="utf8mb4_unicode_ci")

    def __str__(self):
        return self.name
