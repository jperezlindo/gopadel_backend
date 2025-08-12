from django.db import models
from django.core.validators import MinLengthValidator
from django.utils import timezone

class Tournament(models.Model):
    name = models.CharField(
        max_length=100, 
        validators=[MinLengthValidator(2)],
        db_column='name',
        help_text='El nombre debe tener minimo 5 catacteres'
    )
    
    date_start = models.DateTimeField(db_column='date_start')
    date_end = models.DateTimeField(db_column='date_end')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    facility = models.ForeignKey(
        'facilities.Facility',
        on_delete=models.CASCADE,
        related_name='tournaments',
        db_column='facility_id'
    )
    
    def __str__(self):
        return f'{self.name} ({self.date_start} - {self.date_end})'