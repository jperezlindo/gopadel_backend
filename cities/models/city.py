# cities/models/city.py
from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError


class City(models.Model):
    """
    Representa una ciudad (para asociarla a usuarios y facilities).

    Decisiones:
    - Mantengo `cod` como identificador corto (ej. código postal/INEC/propio).
    - Normalizo `name` y `cod` en clean(): trim y `cod` en MAYÚSCULAS.
    - Dejo `cod` único global (uq_city_cod). Si el dominio cambia, se puede
      pasar a unicidad compuesta (name+cod) sin romper demasiado.
    """

    # Datos principales
    name = models.CharField(max_length=15)   # nombre visible (corto para UI)
    cod = models.CharField(max_length=15)    # código interno/externo

    # Banderas de estado
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cities"                       # nombre claro en plural (MySQL)
        verbose_name = "City"
        verbose_name_plural = "Cities"
        default_related_name = "cities"
        ordering = ["name"]                      # orden alfabético por defecto

        # Índices útiles para filtros frecuentes
        indexes = [
            models.Index(fields=["is_active"], name="city_is_active_idx"),
            models.Index(fields=["is_deleted"], name="city_is_deleted_idx"),
            models.Index(fields=["name"],      name="city_name_idx"),
            models.Index(fields=["cod"],       name="city_cod_idx"),
        ]

        # Reglas de negocio / unicidad (MySQL *_ci es case-insensitive)
        constraints = [
            models.CheckConstraint(check=~Q(name=""), name="ck_city_name_not_empty"),
            models.CheckConstraint(check=~Q(cod=""),  name="ck_city_cod_not_empty"),
            models.UniqueConstraint(fields=["cod"], name="uq_city_cod"),
            # Alternativa si se prefiere combinación:
            # models.UniqueConstraint(fields=["name", "cod"], name="uq_city_name_cod"),
        ]

    def __str__(self) -> str:
        return self.name

    # ---------------- Saneamiento / validación ----------------
    def clean(self):
        """
        Aplico normalizaciones y validaciones mínimas:
        - Trim de `name` y `cod` (evito duplicados por espacios).
        - `cod` en MAYÚSCULAS para mantener consistencia y búsquedas.
        """
        if self.name is not None:
            self.name = self.name.strip()
        if self.cod is not None:
            self.cod = self.cod.strip().upper()

        # Validaciones explícitas (además de los CHECK de DB)
        if not self.name:
            raise ValidationError({"name": ["El nombre no puede estar vacío."]})
        if not self.cod:
            raise ValidationError({"cod": ["El código no puede estar vacío."]})

    def save(self, *args, **kwargs):
        """
        Fuerzo full_clean() antes de guardar para que las reglas de clean()
        apliquen también cuando se persiste por ORM (no solo por serializers).
        """
        self.full_clean()
        return super().save(*args, **kwargs)
