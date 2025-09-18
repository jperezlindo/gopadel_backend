# registrations/models/registration_unavailability.py
from django.db import models
from django.db.models import Q, UniqueConstraint, CheckConstraint, F


class RegistrationUnavailability(models.Model):
    """
    Como estrategia de diseño, modelo las indisponibilidades como bloques de tiempo
    (día + rango horario) asociados a una inscripción. Esto me permite:
      - Definir múltiples franjas por día.
      - Evitar modificar el modelo principal con estructuras rígidas.
      - Validar solapes desde el service con reglas claras y testeables.
    """

    # Defino los días como 0..6 (lunes=0, domingo=6) para orden natural e indexación simple.
    class Weekday(models.IntegerChoices):
        MONDAY = 0, "Monday"
        TUESDAY = 1, "Tuesday"
        WEDNESDAY = 2, "Wednesday"
        THURSDAY = 3, "Thursday"
        FRIDAY = 4, "Friday"
        SATURDAY = 5, "Saturday"
        SUNDAY = 6, "Sunday"

    registration = models.ForeignKey(
        "registrations.Registration",
        on_delete=models.CASCADE,
        related_name="unavailability",  # Acceso: registration.unavailability.all()
    )
    day_of_week = models.PositiveSmallIntegerField(choices=Weekday.choices)

    # Uso TimeField para rangos intradía; asumo timezone controlado a nivel app.
    start_time = models.TimeField()
    end_time = models.TimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "registration_unavailability_slots"
        verbose_name = "Registration Unavailability"
        verbose_name_plural = "Registration Unavailability"

        ordering = ["registration_id", "day_of_week", "start_time", "end_time"]

        constraints = [
            # Aseguro rangos válidos
            CheckConstraint(
                check=Q(start_time__lt=F("end_time")),
                name="ck_reg_unav_start_lt_end",
            ),
            # Evito duplicados exactos del mismo bloque
            UniqueConstraint(
                fields=["registration", "day_of_week", "start_time", "end_time"],
                name="uq_reg_unav_exact_block",
            ),
        ]

        indexes = [
            models.Index(fields=["registration"], name="reg_unav_idx_registration"),
            models.Index(fields=["day_of_week"], name="reg_unav_idx_dow"),
            models.Index(fields=["registration", "day_of_week"], name="reg_unav_idx_reg_dow"),
            models.Index(fields=["start_time", "end_time"], name="reg_unav_idx_time"),
        ]

    def __str__(self):
        return f"Unav Reg:{self.registration_id} DOW:{self.day_of_week} {self.start_time}-{self.end_time}" # type: ignore
