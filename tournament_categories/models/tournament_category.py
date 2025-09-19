# tournament_categories/models/tournament_category.py
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q
from tournaments.models.tournament import Tournament
from categories.models.category import Category

class TournamentCategory(models.Model):
    """
    Yo modelo la categoría (rama) de un torneo.
    - name: nombre visible de la categoría en el contexto del torneo (p.ej. "4ta", "Mixto B").
    - price: precio de inscripción asociado a esta categoría dentro del torneo.
    - category: vínculo opcional a Category “maestra” (catálogo global), si aplica.
    """

    name = models.CharField(max_length=30, db_column="name")
    price = models.DecimalField(max_digits=10, decimal_places=2, db_column="price", default=0) # type: ignore
    comment = models.TextField(blank=True, null=True, db_column="comment")

    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name="tournament_categories",
        db_column="tournament_id",
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tournament_categories",
        db_column="category_id",
    )

    is_active = models.BooleanField(default=True, db_column="is_active")
    created_at = models.DateTimeField(auto_now_add=True, db_column="created_at")
    updated_at = models.DateTimeField(auto_now=True, db_column="updated_at")

    class Meta:
        db_table = "tournament_categories"
        verbose_name = "Tournament Category"
        verbose_name_plural = "Tournament Categories"
        default_related_name = "tournament_categories"

        # Yo ordeno primero por torneo (id) y luego por nombre para listados estables.
        ordering = ["tournament_id", "name"]

        # Índices útiles para filtros frecuentes
        indexes = [
            models.Index(fields=["tournament", "is_active"], name="tc_tourn_active_idx"),
            models.Index(fields=["tournament", "name"],      name="tc_tourn_name_idx"),
            models.Index(fields=["category"],                name="tc_category_idx"),
            models.Index(fields=["is_active"],               name="tc_is_active_idx"),
        ]

        # Reglas de negocio:
        constraints = [
            # Un nombre no puede repetirse dentro del mismo torneo
            models.UniqueConstraint(fields=["tournament", "name"], name="unique_name_per_tournament"),
            # Checks de dominio
            models.CheckConstraint(check=~Q(name=""), name="ck_tc_name_not_empty"),
            models.CheckConstraint(check=Q(price__gte=0), name="ck_tc_price_ge_0"),
        ]

    def clean(self):
        """
        Yo normalizo y valido antes de guardar cuando me llamen con full_clean().
        - Hago strip de name para evitar duplicados por espacios.
        - Valido no vacío y no solo espacios.
        - Garantizo price >= 0 (redundante con CHECK, pero útil para feedback temprano).
        """
        # Normalizo el nombre
        self.name = (self.name or "").strip()

        errors = {}

        if not self.name:
            errors["name"] = ["Name is required."]

        # Valido longitud por si llega desfasado del serializer
        if self.name and len(self.name) > 30:
            errors["name"] = errors.get("name", []) + ["Name must be at most 30 characters long."]

        if self.price is not None and self.price < 0:
            errors["price"] = ["Price must be ≥ 0."]

        if errors:
            raise ValidationError(errors)

    def __str__(self) -> str:
        # Yo evito resolver relaciones si no están cargadas, pero acá
        # no es crítico; lo dejo simple y legible.
        cat = getattr(self.category, "name", "NoCategory")
        return f"{self.name} - ({self.tournament_id}) ({cat})" # type: ignore
