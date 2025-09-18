# roles/models/rol.py
from django.db import models
from django.db.models import Q


class Rol(models.Model):
    """
    Representa los distintos roles funcionales del sistema GoPadel.
    Roles esperados en producción:
    - ADMIN: dueño del facility (gestiona torneos y organización).
    - EMPLOYEE: empleado que carga resultados y genera llaves.
    - PLAYER: jugador que se inscribe y sigue el progreso de los torneos.
    Nota: el rol "superusuario" lo maneja Django desde el admin por defecto.
    """

    # Nombre corto y único del rol (ej: "ADMIN", "EMPLOYEE", "PLAYER").
    name = models.CharField(max_length=15, unique=True)

    # Flags de control para habilitar/deshabilitar o aplicar soft delete.
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    # Timestamps automáticos.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Nombre explícito en la base (plural claro).
        db_table = "roles"
        verbose_name = "Role"
        verbose_name_plural = "Roles"
        default_related_name = "roles"

        # Ordeno alfabéticamente los roles por nombre, útil para listados en UI.
        ordering = ["name"]

        # Índices comunes para performance en filtros típicos.
        indexes = [
            models.Index(fields=["is_active"], name="role_is_active_idx"),
            models.Index(fields=["is_deleted"], name="role_is_deleted_idx"),
            models.Index(fields=["name"], name="role_name_idx"),
        ]

        # Constraints para robustez en base de datos.
        constraints = [
            models.CheckConstraint(check=~Q(name=""), name="ck_role_name_not_empty"),
            # Aseguro unicidad global del nombre (además de unique=True en el campo).
            models.UniqueConstraint(fields=["name"], name="uq_role_name"),
        ]

    def __str__(self):
        """
        Representación legible del rol.
        Uso el nombre ya que es único y suficientemente descriptivo.
        """
        return self.name
