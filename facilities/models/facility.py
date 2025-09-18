# facilities/models/facility.py
from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator


class Facility(models.Model):
    """
    Representa un club/cancha de pádel que organiza torneos.

    Decisiones:
    - Se mantiene 'maps' y 'logo' como CharField para no romper compatibilidad,
      pero se valida el formato de URL en clean() si viene valor.
    - 'courts' permite 0 (según constraint), útil si se registra el facility
      antes de cargar canchas; si más adelante se exige al menos 1, se cambia
      el CHECK a >= 1 o se usa MinValueValidator(1).
    """

    # Identificación y datos básicos del lugar
    name = models.CharField(max_length=50)            # nombre comercial del facility
    address = models.CharField(max_length=100)        # dirección postal
    courts = models.IntegerField()                    # cantidad de canchas (>= 0 por constraint)

    # Metadatos opcionales (URLs o rutas a recursos)
    maps = models.CharField(max_length=255, blank=True, null=True)  # URL Google Maps u otro mapa
    logo = models.CharField(max_length=255, blank=True, null=True)  # URL o path del logo

    # Banderas de estado y housekeeping
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)  # se setea al crear
    updated_at = models.DateTimeField(auto_now=True)      # se actualiza en cada save

    class Meta:
        # Nombre explícito en base y convención plural
        db_table = "facilities"
        verbose_name = "Facility"
        verbose_name_plural = "Facilities"
        default_related_name = "facilities"

        # Listado alfabético por defecto para UI
        ordering = ["name"]

        # Índices típicos para filtros frecuentes
        indexes = [
            models.Index(fields=["is_active"],  name="facility_is_active_idx"),
            models.Index(fields=["is_deleted"], name="facility_is_deleted_idx"),
            models.Index(fields=["name"],       name="facility_name_idx"),
        ]

        # Invariantes de negocio y calidad de datos (MySQL 8 respeta CHECK)
        constraints = [
            models.CheckConstraint(check=~Q(name=""),    name="ck_facility_name_not_empty"),
            models.CheckConstraint(check=~Q(address=""), name="ck_facility_address_not_empty"),
            models.CheckConstraint(check=Q(courts__gte=0), name="ck_facility_courts_non_negative"),
            # Se asume (name, address) único para evitar duplicados del mismo lugar.
            models.UniqueConstraint(fields=["name", "address"], name="uq_facility_name_address"),
            # Si en el futuro se desea nombre global único, reemplazar por:
            # models.UniqueConstraint(fields=["name"], name="uq_facility_name"),
        ]

    def __str__(self) -> str:
        """
        Representación legible del facility.
        Se usa el nombre, suficiente para listados y logs.
        """
        return self.name

    # ---------------- Validaciones y saneamiento ----------------

    def clean(self):
        """
        Centralizo validaciones y normalizaciones:
        - name/address: trim para evitar duplicados por espacios.
        - courts: refuerzo la regla de no-negativo además del CHECK de DB.
        - maps/logo: si vienen valores, valido formato de URL.
        """
        url_validator = URLValidator()

        # Normalizo strings básicos
        if self.name is not None:
            self.name = self.name.strip()
        if self.address is not None:
            self.address = self.address.strip()

        # Regla explícita sobre courts (además del CHECK de DB)
        if self.courts is None:
            raise ValidationError({"courts": ["Este campo es obligatorio."]})
        if self.courts < 0:
            raise ValidationError({"courts": ["La cantidad de canchas no puede ser negativa."]})

        # Valido formato de URL si hay valor
        if self.maps:
            try:
                url_validator(self.maps)
            except ValidationError:
                raise ValidationError({"maps": ["Debe ser una URL válida."]})

        if self.logo:
            try:
                url_validator(self.logo)
            except ValidationError:
                raise ValidationError({"logo": ["Debe ser una URL válida."]})

    def save(self, *args, **kwargs):
        """
        Fuerzo full_clean() antes de guardar para que las reglas de clean()
        apliquen también cuando se persiste por ORM (no solo por serializers).
        """
        self.full_clean()
        return super().save(*args, **kwargs)
