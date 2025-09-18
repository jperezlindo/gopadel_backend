# players/models/player.py
from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from categories.models.category import Category
from users.models.user import CustomUser


class Player(models.Model):
    """
    Representa el perfil de jugador asociado 1:1 a un CustomUser.
    Decisiones:
    - Relación OneToOne con User (un usuario tiene un solo player).
    - `nick_name` indexado para búsquedas. No obligo unicidad global porque
      puede haber nicks repetidos; si el negocio lo exige más adelante, se agrega.
    - `position` opcional (REVES/DRIVE).
    - `level` y `points` opcionales; valido no-negatividad suave.
    """

    REVES = "REVES"
    DRIVE = "DRIVE"
    position_choices = [
        (REVES, "Reves"),
        (DRIVE, "Drive"),
    ]

    nick_name = models.CharField(max_length=30, db_index=True)
    position = models.CharField(max_length=8, choices=position_choices, null=True, blank=True)
    level = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    points = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,           # al borrar el user, se borra el player
        related_name="player",
        db_index=True,
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,          # si se borra la categoría, se mantiene el player
        related_name="players",
        db_index=True,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "players"
        verbose_name = "Player"
        verbose_name_plural = "Players"
        default_related_name = "players"
        ordering = ["nick_name"]

        indexes = [
            models.Index(fields=["is_active"], name="player_is_active_idx"),
            models.Index(fields=["nick_name"], name="player_nick_name_idx"),
        ]

        constraints = [
            models.CheckConstraint(check=~Q(nick_name=""), name="ck_player_nick_not_empty"),
            models.CheckConstraint(check=Q(points__gte=0) | Q(points__isnull=True), name="ck_player_points_ge0"),
            # Rango opcional para level si el negocio lo requiere:
            # models.CheckConstraint(
            #     check=(Q(level__gte=0.0) & Q(level__lte=10.0)) | Q(level__isnull=True),
            #     name="ck_player_level_range",
            # ),
        ]

    def __str__(self) -> str:
        return self.nick_name

    # ---------------- Validaciones y saneamiento ----------------
    def clean(self):
        """
        Normalizo y valido datos clave:
        - nick_name con trim (evito dobles espacios).
        - points no negativo (refuerzo además del CHECK).
        """
        if self.nick_name is not None:
            self.nick_name = self.nick_name.strip()

        if self.points is not None and self.points < 0:
            raise ValidationError({"points": ["Los puntos no pueden ser negativos."]})

    def save(self, *args, **kwargs):
        """
        Fuerzo full_clean() antes de guardar para que las reglas de clean()
        apliquen también cuando se persiste por ORM.
        """
        self.full_clean()
        return super().save(*args, **kwargs)
