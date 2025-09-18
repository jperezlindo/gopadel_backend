# tournaments/models/tournament.py
from django.db import models
from django.core.validators import MinLengthValidator
from django.core.exceptions import ValidationError
from django.db.models import Q


class Tournament(models.Model):
    """
    Representa un torneo de pádel organizado por un Facility.

    Decisiones:
    - Unifico mínimo del nombre a 5 caracteres (coherente con help_text).
    - Valido fechas y normalizo name en clean().
    - Agrego constraint de unicidad (facility + name + date_start) para evitar duplicados comunes.
    - Dejo preparado (comentado) un chequeo de solapamiento por facility, por si el negocio lo exige.
    """

    name = models.CharField(
        max_length=100,
        validators=[MinLengthValidator(5)],  # unifico con el help_text
        db_column="name",
        help_text="El nombre debe tener mínimo 5 caracteres",
    )

    date_start = models.DateTimeField(db_column="date_start")
    date_end = models.DateTimeField(db_column="date_end")

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    facility = models.ForeignKey(
        "facilities.Facility",
        on_delete=models.CASCADE,
        related_name="tournaments",
        db_column="facility_id",
    )

    class Meta:
        db_table = "tournaments"
        verbose_name = "Tournament"
        verbose_name_plural = "Tournaments"
        default_related_name = "tournaments"
        ordering = ["-date_start", "-id"]

        indexes = [
            models.Index(fields=["facility"], name="tourn_facility_idx"),
            models.Index(fields=["is_active"], name="tourn_is_active_idx"),
            models.Index(fields=["date_start"], name="tourn_date_start_idx"),
            models.Index(fields=["date_end"], name="tourn_date_end_idx"),
            models.Index(fields=["facility", "is_active"], name="tourn_facility_active_idx"),
        ]

        constraints = [
            models.CheckConstraint(check=~Q(name=""), name="ck_tournament_name_not_empty"),
            models.CheckConstraint(check=Q(date_end__gte=models.F("date_start")), name="ck_tournament_dates_valid"),
            # Evito duplicados típicos: mismo facility, mismo nombre y misma fecha de inicio
            models.UniqueConstraint(fields=["facility", "name", "date_start"], name="uq_tournament_fac_name_start"),
        ]

    def __str__(self):
        return f"{self.name} ({self.date_start} - {self.date_end})"

    # ---------------- Validaciones / saneamiento ----------------
    def clean(self):
        """
        - Normalizo name (trim).
        - Refuerzo regla de fechas (además del CHECK).
        - (Opcional) Chequeo de solapamiento por facility si el negocio lo pide.
        """
        if self.name is not None:
            self.name = self.name.strip()

        if self.date_end and self.date_start and self.date_end < self.date_start:
            raise ValidationError({"date_end": ["La fecha de fin no puede ser anterior a la fecha de inicio."]})

        # --- Ejemplo de chequeo de solapamiento por facility (opcional) ---
        # if self.facility_id and self.date_start and self.date_end:
        #     overlap = Tournament.objects.filter(
        #         facility_id=self.facility_id,
        #         date_start__lte=self.date_end,
        #         date_end__gte=self.date_start,
        #     )
        #     if self.pk:
        #         overlap = overlap.exclude(pk=self.pk)
        #     if overlap.exists():
        #         raise ValidationError({"date_start": ["Existe otro torneo del mismo facility que se solapa en fechas."]})

    def save(self, *args, **kwargs):
        """
        Hago full_clean() antes de guardar para aplicar clean() también cuando
        se persiste directo por ORM (no solo por serializers).
        """
        self.full_clean()
        return super().save(*args, **kwargs)
