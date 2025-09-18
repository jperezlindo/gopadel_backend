# registrations/models/registration.py
from django.db import models
from django.core.validators import MinValueValidator
from django.db.models import Q, UniqueConstraint, CheckConstraint, F


class Registration(models.Model):
    """
    Como responsable del dominio, defino el registro de una pareja (player + partner)
    en una TournamentCategory. Mantengo este modelo enfocado en datos de negocio
    directos (pago, estado, etc.) y delego la gestión de indisponibilidades horarias
    a un modelo hijo (RegistrationUnavailability) para permitir múltiples franjas.
    """

    tournament_category = models.ForeignKey(
        "tournament_categories.TournamentCategory",
        on_delete=models.CASCADE,
        related_name="registrations",
    )
    player = models.ForeignKey(
        "players.Player",
        on_delete=models.CASCADE,
        related_name="registrations_as_player",
    )
    partner = models.ForeignKey(
        "players.Player",
        on_delete=models.CASCADE,
        related_name="registrations_as_partner",
    )

    paid_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    payment_reference = models.TextField(blank=True, default="")
    comment = models.CharField(max_length=255, blank=True, default="")

    is_active = models.BooleanField(default=True)
    payment_status = models.CharField(max_length=50, blank=True, default="")  # sin choices para no forzar validación

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "registrations"

        # Legibilidad y convenciones
        verbose_name = "Registration"
        verbose_name_plural = "Registrations"
        default_related_name = "registrations"

        # Orden y "latest"
        ordering = ["-created_at", "-id"]
        get_latest_by = "created_at"

        # Reglas a nivel BD
        constraints = [
            # un jugador no puede inscribirse 2 veces en la misma TC
            UniqueConstraint(
                fields=["tournament_category", "player"],
                name="uq_registration_tc_player",
            ),
            # un partner no puede repetirse en la misma TC
            UniqueConstraint(
                fields=["tournament_category", "partner"],
                name="uq_registration_tc_partner",
            ),
            # par (player, partner) único por TC (orden inverso se valida en service)
            UniqueConstraint(
                fields=["tournament_category", "player", "partner"],
                name="uq_registration_tc_player_partner",
            ),
            # player != partner
            CheckConstraint(
                check=~Q(player=F("partner")),
                name="ck_registration_player_ne_partner",
            ),
            # paid_amount >= 0 (refuerza el validator a nivel BD)
            CheckConstraint(
                check=Q(paid_amount__gte=0),
                name="ck_registration_paid_amount_gte_0",
            ),
        ]

        # Índices para consultas típicas
        indexes = [
            models.Index(fields=["tournament_category"], name="reg_idx_tc"),
            models.Index(fields=["player"], name="reg_idx_player"),
            models.Index(fields=["partner"], name="reg_idx_partner"),
            models.Index(fields=["is_active"], name="reg_idx_is_active"),
            models.Index(fields=["payment_status"], name="reg_idx_payment_status"),
            models.Index(fields=["-created_at", "-id"], name="reg_idx_created_desc"),
        ]

    def __str__(self):
        # Mantengo una representación concisa y útil para logs/admin
        return f"Reg #{self.pk} - TC:{self.tournament_category_id} P:{self.player_id}/{self.partner_id}"  # type: ignore

    # --- Helpers de dominio (no obligatorios, pero útiles) ---
    @property
    def weekday_unavailability(self):
        """
        Expongo un acceso rápido a las indisponibilidades (solo días de semana).
        Esto me sirve para componer lógica en servicios/serializers sin duplicar queries.
        """
        return self.unavailability.filter(day_of_week__in=[0, 1, 2, 3, 4]).order_by("day_of_week", "start_time") # type: ignore
