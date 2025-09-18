# users/repositories/user_repository.py
from typing import Any, Optional
from django.core.exceptions import ObjectDoesNotExist
from users.models.user import CustomUser
from users.interfaces.user_repository_interface import UserRepositoryInterface


class UserRepository(UserRepositoryInterface):
    """
    Centralizo el acceso a datos de CustomUser para mantener los controllers
    y services desacoplados del ORM.

    Convenciones del repo:
    - get_all_users: devuelvo solo usuarios activos, no eliminados y que no sean superusers.
    - get_user_by_id: permito recuperar usuarios inactivos (para poder reactivarlos),
      pero sigo excluyendo eliminados lógicos.
    - create_user: delego en el manager para asegurar hash de password y defaults coherentes.
    - update_user: nunca toco el password (existe flujo dedicado para eso).
    - delete_user: implemento soft-delete (is_deleted=True) y desactivo el usuario (is_active=False).
    """

    def _base_qs(self):
        """
        Defino un queryset base consistente:
        - Uso select_related para evitar N+1 en facility/city/rol/player.
        - Por defecto excluyo eliminados lógicos.
        """
        return (
            CustomUser.objects
            .select_related("facility", "city", "rol", "player")
            .filter(is_deleted=False)
        )

    def get_all_users(self) -> Any:
        """
        Listo usuarios visibles en UI operativa:
        - Activos: True
        - No eliminados: True
        - No superusuarios: para evitar exponer cuentas administrativas
        """
        return (
            self._base_qs()
            .filter(is_active=True, is_superuser=False)
        )

    def get_user_by_id(self, user_id: int) -> Optional[CustomUser]:
        """
        Busco por PK respetando soft-delete:
        - Incluyo usuarios inactivos (para poder reactivarlos desde un panel),
          pero no incluyo eliminados lógicos.
        - Si no existe, retorno None (la capa service decide si levanta not_found).
        """
        try:
            return (
                self._base_qs()
                .get(id=user_id)
            )
        except ObjectDoesNotExist:
            return None

    def create_user(self, data: dict) -> CustomUser:
        """
        Creo un usuario delegando en el manager:
        - Si viene password en data, el manager lo hashea.
        - Si no viene, fallo explícitamente a nivel manager (regla coherente con create_user).
        """
        password = data.pop("password", None)
        if password is not None:
            return CustomUser.objects.create_user(password=password, **data)  # type: ignore[arg-type]
        # Mantengo la misma decisión: create_user exige password (evito cuentas sin credenciales).
        return CustomUser.objects.create_user(**data)  # type: ignore[arg-type]

    def update_user(self, user_id: int, data: dict) -> Optional[CustomUser]:
        """
        Actualizo campos simples del usuario, sin tocar password.
        - Saneo email (trim + lower) si viene en data.
        - Aplico lista blanca de campos permitidos para evitar modificaciones indeseadas.
        """
        user = self.get_user_by_id(user_id)
        if user is None:
            return None

        # Nunca toco password acá (existe un endpoint/flujo dedicado).
        data.pop("password", None)

        # Normalizo email si viene
        if "email" in data and data["email"]:
            data["email"] = str(data["email"]).strip().lower()

        allowed_fields = [
            "name", "last_name", "email", "birth_day", "avatar",
            "is_active", "facility_id", "city_id", "rol_id"
        ]
        for key, value in data.items():
            if key in allowed_fields:
                setattr(user, key, value)

        user.save()
        return user

    def delete_user(self, user_id: int) -> bool:
        """
        Implemento soft-delete:
        - Marco is_deleted=True y desactivo is_active=False.
        - Retorno bool para que la capa service/controller pueda responder 404 si es False.
        """
        user = self.get_user_by_id(user_id)
        if user is None:
            return False
        user.is_deleted = True
        user.is_active = False
        user.save(update_fields=["is_deleted", "is_active", "updated_at"])
        return True
