# players/models/player.py
from django.db import models
from django.db.models import Q
from categories.models.category import Category
from users.models.user import CustomUser

class Player(models.Model):
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
        on_delete=models.CASCADE,
        related_name="player",
        db_index=True,
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        related_name="players",
        db_index=True,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "players"                 # 👈 nombre claro en plural (MySQL)
        verbose_name = "Player"
        verbose_name_plural = "Players"
        default_related_name = "players"
        ordering = ["nick_name"]            # orden alfabético por defecto

        # Índices para filtros/búsquedas frecuentes
        indexes = [
            models.Index(fields=["is_active"], name="player_is_active_idx"),
            models.Index(fields=["nick_name"], name="player_nick_name_idx"),
            # user y category ya tienen índice propio (FK/OneToOne), lo dejamos así
        ]

        # Checks suaves (MySQL 8 los respeta)
        constraints = [
            models.CheckConstraint(check=~Q(nick_name=""), name="ck_player_nick_not_empty"),
            models.CheckConstraint(check=Q(points__gte=0) | Q(points__isnull=True), name="ck_player_points_ge0"),
            # Si quisieras acotar level (ej. 0.0 a 10.0), podemos activar algo como:
            # models.CheckConstraint(
            #     check=(Q(level__gte=0.0) & Q(level__lte=10.0)) | Q(level__isnull=True),
            #     name="ck_player_level_range",
            # ),
        ]

    def __str__(self) -> str:
        return self.nick_name
