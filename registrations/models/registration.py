# registrations/models/registration.py
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from tournaments.models.tournament import Tournament
from tournament_categories.models.tournament_category import TournamentCategory
from players.models.player import Player

class Registration(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"

    class PaymentStatus(models.TextChoices):
        UNPAID = "unpaid", "Unpaid"
        PAID = "paid", "Paid"
        REFUNDED = "refunded", "Refunded"

    tournament_category = models.ForeignKey(
        TournamentCategory, on_delete=models.CASCADE, related_name="registrations"
    )
    player = models.ForeignKey(
        Player, on_delete=models.CASCADE, related_name="registrations_as_player"
    )
    partner = models.ForeignKey(
        Player, on_delete=models.CASCADE, related_name="registrations_as_partner"
    )

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    
    payment_status = models.CharField(
        max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID
    )
    
    paid_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)] # type: ignore
    )
    
    payment_reference = models.CharField(max_length=120, blank=True, null=True)
    
    comment = models.TextField(blank=True, null=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "registrations_registration"
        # Orden canónico de la pareja: player_id < partner_id
        constraints = [
            models.CheckConstraint(
                check=models.Q(player__lt=models.F("partner")),
                name="registrations_player_lt_partner",
            ),
            # Unicidad de la pareja (orden canónico) dentro de la misma tournament_category
            models.UniqueConstraint(
                fields=["tournament_category", "player", "partner"],
                name="uq_registration_pair_in_category",
            ),
        ]
        indexes = [
            models.Index(fields=["tournament_category"]),
            models.Index(fields=["player"]),
            models.Index(fields=["partner"]),
        ]

    def __str__(self) -> str:
        return f"Reg #{self.pk} - TC:{self.tournament_category_id} [{self.player_id}+{self.partner_id}]" # type: ignore
