from django.db import models

class City(models.Model):
    name = models.CharField(max_length=15)
    cod = models.CharField(max_length=15)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
