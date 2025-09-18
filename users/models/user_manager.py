# users/models/user_manager.py
from django.contrib.auth.models import BaseUserManager
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """
    Defino el manager para crear usuarios y superusuarios con email como
    identificador. Se normaliza el email y se aplican defaults seguros.
    """

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        """
        Creo un usuario estándar:
        - Exijo email y password (evito cuentas sin credenciales).
        - Normalizo el email (trim + lower).
        - Seteo flags por defecto: is_staff=False, is_superuser=False, is_active=True.
        """
        if not email:
            raise ValueError(_("The Email field must be set"))
        if password is None:
            raise ValueError(_("The Password field must be set"))

        # Normalizo y trimeo
        email = self.normalize_email(email.strip().lower())

        # Defaults seguros
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_active", True)

        # Creo la instancia usando el modelo asociado al manager
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str, **extra_fields):
        """
        Creo un superusuario:
        - is_staff=True, is_superuser=True, is_active=True
        - Valido coherencia de flags para evitar configuraciones inválidas.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(email, password, **extra_fields)
