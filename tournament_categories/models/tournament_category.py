from django.db import models
from django.core.exceptions import ValidationError
from tournaments.models.tournament import Tournament
from categories.models.category import Category

class TournamentCategory(models.Model):
    name = models.CharField(max_length=30, db_column='name')
    price = models.DecimalField(max_digits=10, decimal_places=2, db_column='price', default=0)
    comment = models.TextField(blank=True, null=True, db_column='comment')

    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name='tournament_categories',
        db_column='tournament_id',
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,            # antes: CASCADE
        null=True,                            # permitir nulos
        blank=True,                           # permitir vacío en formularios
        related_name='tournament_categories',
        db_column='category_id',
    )
    
    is_active = models.BooleanField(default=True, db_column='is_active')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')
    
    class Meta:
        db_table = 'tournament_categories'
        verbose_name = 'Tournament Category'
        verbose_name_plural = 'Tournament Categories'
        constraints = [
            models.UniqueConstraint(fields=['tournament', 'name'], name='unique_name_per_tournament')
        ]

    def clean(self):
        if self.price is not None and self.price < 0:
            raise ValidationError({'price': 'Price must be ≥ 0.'})
        if not self.name or not self.name.strip():
            raise ValidationError({'name': 'Name is required.'})
        
    def __str__(self) -> str:
        cat = self.category.name if self.category else 'NoCategory'
        return f"{self.name} - ({self.tournament.name}) ({cat})"
