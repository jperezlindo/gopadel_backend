# users/repositories/user_repository.py
from typing import Any, Optional
from django.core.exceptions import ObjectDoesNotExist
from users.models.user import CustomUser
from users.interfaces.user_repository_interface import UserRepositoryInterface


class UserRepository(UserRepositoryInterface):
    """
    Acceso a datos para CustomUser.

    Convenciones:
    - get_all_users: lista usuarios activos y no eliminados (y no superusers).
    - get_user_by_id: trae incluso inactivos (solo excluye eliminados) para poder reactivarlos.
    - create_user: usa el manager para hashear password si viene en data.
    - update_user: no modifica password.
    - delete_user: soft delete (is_deleted=True) + desactiva (is_active=False) y retorna bool.
    """

    def get_all_users(self) -> Any:
        return (
            CustomUser.objects
            .select_related("facility", "city", "rol", "player")
            .filter(is_active=True, is_deleted=False, is_superuser=False)
        )

    def get_user_by_id(self, user_id: int) -> Optional[CustomUser]:
        try:
            return (
                CustomUser.objects
                .select_related("facility", "city", "rol", "player")
                .get(id=user_id, is_deleted=False)
            )
        except ObjectDoesNotExist:
            return None

    def create_user(self, data: dict) -> CustomUser:
        # Usamos el manager para asegurar hash de password y defaults
        password = data.pop("password", None)
        if password is not None:
            return CustomUser.objects.create_user(password=password, **data) # type: ignore
        return CustomUser.objects.create_user(**data)  # type: ignore[arg-type]

    def update_user(self, user_id: int, data: dict) -> Optional[CustomUser]:
        user = self.get_user_by_id(user_id)
        if user is None:
            return None

        # Nunca tocamos password aquí (endpoint dedicado)
        data.pop("password", None)

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
        user = self.get_user_by_id(user_id)
        if user is None:
            return False
        user.is_deleted = True
        user.is_active = False
        user.save()
        return True
