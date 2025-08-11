from typing import Any, Optional
from django.core.exceptions import ObjectDoesNotExist
from users.models.user import CustomUser
from users.interfaces.user_repository_interface import UserRepositoryInterface


class UserRepository(UserRepositoryInterface):
    """
    Repository to manage data access for CustomUser.
    """

    def get_all_users(self) -> Any:
        return CustomUser.objects.filter(is_active=True, is_deleted=False, is_superuser=False)

    def get_user_by_id(self, user_id: int) -> Optional[CustomUser]:
        try:
            return CustomUser.objects.get(id=user_id, is_deleted=False, is_active=True)
        except ObjectDoesNotExist:
            return None

    def create_user(self, data: dict) -> CustomUser:
        return CustomUser.objects.create_user(**data) # type: ignore

    def update_user(self, user_id: int, data: dict) -> Optional[CustomUser]:
        user = self.get_user_by_id(user_id)
        if user is None:
            return None

        allowed_fields = [
            "name", "last_name", "email", "birth_day", "avatar",
            "is_active", "facility_id", "city_id", "rol_id"
        ]

        for key, value in data.items():
            if key in allowed_fields:
                setattr(user, key, value)

        user.save()
        return user

    def delete_user(self, user_id: int) -> Optional[CustomUser]:
        user = self.get_user_by_id(user_id)
        if user is None:
            return None

        user.is_deleted = True
        user.save()
        return user
