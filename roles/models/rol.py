
# roles/models/rol.py
from django.db import models
from django.db.models import Q

class Rol(models.Model):
    name = models.CharField(max_length=15)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "roles"                   # 👈 nombre claro en plural (MySQL)
        verbose_name = "Role"
        verbose_name_plural = "Roles"
        default_related_name = "roles"
        ordering = ["name"]                  # orden alfabético por defecto

        indexes = [
            models.Index(fields=["is_active"],  name="role_is_active_idx"),
            models.Index(fields=["is_deleted"], name="role_is_deleted_idx"),
            models.Index(fields=["name"],       name="role_name_idx"),
        ]

        constraints = [
            models.CheckConstraint(check=~Q(name=""), name="ck_role_name_not_empty"),
            # Si querés nombre único global (recomendado), dejá esta constraint:
            models.UniqueConstraint(fields=["name"], name="uq_role_name"),
        ]

    def __str__(self):
        return self.name
