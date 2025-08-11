from django.db import models

class Facility(models.Model):
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=100)
    courts = models.IntegerField()
    maps = models.CharField(max_length=255, blank=True, null=True)
    logo = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
