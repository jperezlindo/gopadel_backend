# users/models/user.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from users.models.user_manager import CustomUserManager
from facilities.models import Facility
from cities.models import City
from roles.models import Rol
from django.db.models import Q

class CustomUser(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(max_length=50, unique=True)
    birth_day = models.DateField(null=True, blank=True)
    avatar = models.CharField(max_length=255, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    facility = models.ForeignKey(
        Facility,
        on_delete=models.SET_NULL,
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

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "last_name"]

    objects = CustomUserManager()

    class Meta:
        db_table = "users"                 # nombre claro en plural (MySQL)
        verbose_name = "User"
        verbose_name_plural = "Users"
        default_related_name = "users"
        ordering = ["-created_at", "id"]   # últimos creados primero

        # Índices típicos para filtros/búsquedas
        indexes = [
            models.Index(fields=["email"],      name="user_email_idx"),
            models.Index(fields=["is_active"],  name="user_is_active_idx"),
            models.Index(fields=["is_deleted"], name="user_is_deleted_idx"),
            models.Index(fields=["facility"],   name="user_facility_idx"),
            models.Index(fields=["city"],       name="user_city_idx"),
            models.Index(fields=["rol"],        name="user_rol_idx"),
        ]

        # Reglas de negocio / saneamiento (MySQL 8 soporta CHECK)
        constraints = [
            models.CheckConstraint(check=~Q(name=""),      name="ck_user_name_not_empty"),
            models.CheckConstraint(check=~Q(last_name=""), name="ck_user_last_name_not_empty"),
            # Email ya es unique=True; con collation *_ci es case-insensitive
        ]

    def __str__(self):
        return self.email
