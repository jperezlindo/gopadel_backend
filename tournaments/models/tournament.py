# tournaments/models/tournament.py
from django.db import models
from django.core.validators import MinLengthValidator
from django.db.models import Q

class Tournament(models.Model):
    name = models.CharField(
        max_length=100,
        validators=[MinLengthValidator(2)],  # Nota: tu help_text dice 5, acá sigue 2
        db_column="name",
        help_text="El nombre debe tener minimo 5 catacteres",
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
        db_table = "tournaments"                 # 👈 nombre claro en plural (MySQL)
        verbose_name = "Tournament"
        verbose_name_plural = "Tournaments"
        default_related_name = "tournaments"
        # Más nuevos primero (por fecha de inicio y, a igualdad, por id)
        ordering = ["-date_start", "-id"]

        # Índices útiles para listados/filtros frecuentes
        indexes = [
            models.Index(fields=["facility"],    name="tourn_facility_idx"),
            models.Index(fields=["is_active"],   name="tourn_is_active_idx"),
            models.Index(fields=["date_start"],  name="tourn_date_start_idx"),
            models.Index(fields=["date_end"],    name="tourn_date_end_idx"),
            models.Index(fields=["facility", "is_active"], name="tourn_facility_active_idx"),
        ]

        # Reglas de negocio (MySQL 8 soporta CHECK)
        constraints = [
            models.CheckConstraint(check=~Q(name=""), name="ck_tournament_name_not_empty"),
            models.CheckConstraint(check=Q(date_end__gte=models.F("date_start")), name="ck_tournament_dates_valid"),
        ]

    def __str__(self):
        return f"{self.name} ({self.date_start} - {self.date_end})"
