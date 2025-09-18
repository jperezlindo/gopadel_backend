# users/models/user.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db.models import Q
from django.core.exceptions import ValidationError

from users.models.user_manager import CustomUserManager
from facilities.models import Facility
from cities.models import City
from roles.models import Rol


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Defino el modelo de usuario custom para manejar autenticación por email,
    referencias a Facility/City/Rol, y banderas de estado (is_active/is_deleted/is_staff).

    Decisiones clave:
    - Se usa AbstractBaseUser + PermissionsMixin para tener control total sobre el esquema.
    - El email es el USERNAME_FIELD para login con JWT.
    - Se agrega soft-delete (is_deleted) para futuras necesidades de auditoría.
    """

    # Datos personales básicos
    name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(max_length=50, unique=True)  # único para login
    birth_day = models.DateField(null=True, blank=True)
    avatar = models.CharField(max_length=255, null=True, blank=True)  # URL/path a imagen

    # Banderas de estado
    is_active = models.BooleanField(default=True)    # requerido por Django auth
    is_deleted = models.BooleanField(default=False)  # soft-delete para ocultar sin perder histórico
    is_staff = models.BooleanField(default=False)    # acceso al admin

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)  # se setea al crear
    updated_at = models.DateTimeField(auto_now=True)      # se actualiza en cada save

    # Relaciones con otras entidades del dominio
    facility = models.ForeignKey(
        Facility,
        on_delete=models.SET_NULL,  # al borrar facility, se preserva el usuario
        null=True,
        blank=True,
        related_name="users",
    )
    city = models.ForeignKey(
        City,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )
    rol = models.ForeignKey(
        Rol,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )

    # Configuración de autenticación
    USERNAME_FIELD = "email"                 # login con email
    REQUIRED_FIELDS = ["name", "last_name"]  # campos obligatorios al crear superuser

    # Manager custom con create_user / create_superuser
    objects = CustomUserManager()

    class Meta:
        # Defino metadata de tabla, naming e índices para consultas comunes.
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"
        default_related_name = "users"       # relaciones inversas por defecto
        ordering = ["-created_at", "id"]     # últimos creados primero

        # Índices típicos para performance de filtros/búsquedas
        indexes = [
            models.Index(fields=["email"],      name="user_email_idx"),
            models.Index(fields=["is_active"],  name="user_is_active_idx"),
            models.Index(fields=["is_deleted"], name="user_is_deleted_idx"),
            models.Index(fields=["facility"],   name="user_facility_idx"),
            models.Index(fields=["city"],       name="user_city_idx"),
            models.Index(fields=["rol"],        name="user_rol_idx"),
        ]

        # Reglas de saneamiento a nivel DB (MySQL 8 soporta CHECK)
        constraints = [
            models.CheckConstraint(check=~Q(name=""),      name="ck_user_name_not_empty"),
            models.CheckConstraint(check=~Q(last_name=""), name="ck_user_last_name_not_empty"),
            # El email ya es unique=True; con collation *_ci queda case-insensitive en MySQL.
        ]

    # ---------------- Métodos de dominio / utilitarios ----------------

    def __str__(self) -> str:
        # Expongo el email como representación canónica para logs y admin.
        return self.email

    def get_full_name(self) -> str:
        # Devuelvo nombre completo para UI y reporting.
        return f"{self.name} {self.last_name}".strip()

    def get_short_name(self) -> str:
        # Devuelvo nombre corto para listados compactos.
        return self.name

    # ---------------- Validación de datos ----------------

    def clean(self):
        """
        Centralizo validaciones y normalizaciones:
        - Email siempre en minúsculas y sin espacios.
        - Nombre y apellido no deben ser cadenas vacías o solo espacios.
        """
        # Normalizo email (minúsculas + trim)
        if self.email:
            self.email = self.email.strip().lower()

        # Valido nombre y apellido "no vacíos" (evito cadenas de espacios)
        if self.name is not None and not self.name.strip():
            raise ValidationError({"name": ["El nombre no puede estar vacío."]})
        if self.last_name is not None and not self.last_name.strip():
            raise ValidationError({"last_name": ["El apellido no puede estar vacío."]})

    def save(self, *args, **kwargs):
        """
        Fuerzo full_clean() antes de guardar para garantizar que las reglas de
        clean() se apliquen también en creaciones/actualizaciones por ORM.
        """
        self.full_clean()
        return super().save(*args, **kwargs)
