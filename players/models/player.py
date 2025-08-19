from django.db import models
from categories.models.category import Category
from users.models.user import CustomUser

class Player(models.Model):
    REVES = 'REVES'
    DRIVE = 'DRIVE'
    position_choices = [
        (REVES, 'Reves'),
        (DRIVE, 'Drive'),
    ]
    
    nick_name = models.CharField(max_length=30)
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
        db_index=True
    )
    
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        related_name="players",
        db_index=True,
        null=True,
        blank=True
    )
    
    def __str__(self) -> str:
        return self.nick_name