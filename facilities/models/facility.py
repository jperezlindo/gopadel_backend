# facilities/models/facility.py
from django.db import models
from django.db.models import Q

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

    class Meta:
        db_table = "facilities"                 # 👈 nombre claro en plural (MySQL)
        verbose_name = "Facility"
        verbose_name_plural = "Facilities"
        default_related_name = "facilities"
        ordering = ["name"]                     # listado alfabético por defecto

        # Índices típicos para filtros frecuentes
        indexes = [
            models.Index(fields=["is_active"],  name="facility_is_active_idx"),
            models.Index(fields=["is_deleted"], name="facility_is_deleted_idx"),
            models.Index(fields=["name"],       name="facility_name_idx"),
        ]

        # Invariantes de negocio (MySQL 8 respeta CHECK)
        constraints = [
            models.CheckConstraint(check=~Q(name=""),    name="ck_facility_name_not_empty"),
            models.CheckConstraint(check=~Q(address=""), name="ck_facility_address_not_empty"),
            models.CheckConstraint(check=Q(courts__gte=0), name="ck_facility_courts_non_negative"),
            # Si un mismo nombre puede existir en distintas direcciones, dejá esta combinación:
            models.UniqueConstraint(fields=["name", "address"], name="uq_facility_name_address"),
            # Si preferís nombre único global, reemplazá por:
            # models.UniqueConstraint(fields=["name"], name="uq_facility_name"),
        ]

    def __str__(self):
        return self.name
