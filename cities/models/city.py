# cities/models/city.py
from django.db import models
from django.db.models import Q

class City(models.Model):
    name = models.CharField(max_length=15)
    cod = models.CharField(max_length=15)  # código interno/externo (ej. postal/INEC, etc.)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cities"                       # 👈 nombre claro en plural (MySQL)
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
            # Evitar vacíos estrictos (defensa básica a nivel DB)
            models.CheckConstraint(check=~Q(name=""), name="ck_city_name_not_empty"),
            models.CheckConstraint(check=~Q(cod=""),  name="ck_city_cod_not_empty"),

            # Si tu 'cod' es un identificador único de ciudad, esta constraint es ideal:
            models.UniqueConstraint(fields=["cod"], name="uq_city_cod"),

            # Si preferís permitir el mismo 'cod' en distintos contextos, cambia a combinación:
            # models.UniqueConstraint(fields=["name", "cod"], name="uq_city_name_cod"),
        ]

    def __str__(self):
        return self.name
