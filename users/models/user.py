from typing import Any
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from users.models.user_manager import CustomUserManager
from facilities.models import Facility
from cities.models import City
from roles.models import Rol

class CustomUser(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(max_length=50, unique=True)
    birth_day = models.DateField(null=True, blank=True)
    avatar = models.CharField(max_length=255, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)  # ← necesario para el admin

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Relaciones
    facility_id = models.ForeignKey(Facility, on_delete=models.SET_NULL, null=True, blank=True)
    city_id = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    rol_id = models.ForeignKey(Rol, on_delete=models.SET_NULL, null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'last_name']

    objects: CustomUserManager = CustomUserManager() 

    def __str__(self):
        return self.email

