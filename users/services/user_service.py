# users/services/user_service.py
from typing import Any, Optional, Dict
from django.core.exceptions import ValidationError as DjangoValidationError

from users.models.user import CustomUser
from users.repositories.user_repository import UserRepository


class UserService:
    def __init__(self, repository: Optional[UserRepository] = None):
        self.repository = repository or UserRepository()

    def list(self) -> Any:
        return self.repository.get_all_users()

    def get(self, user_id: int) -> CustomUser:
        instance = self.repository.get_user_by_id(user_id)
        if not instance:
            raise DjangoValidationError({"detail": "User not found."})
        return instance

    def create(self, data: Dict) -> CustomUser:
        instance = self.repository.create_user(data)
        # Validaciones de modelo (si algo falla, levanta DjangoValidationError)
        instance.full_clean()
        instance.save()
        return instance

    def update(self, user_id: int, data: Dict) -> CustomUser:
        instance = self.repository.update_user(user_id, data)
        if not instance:
            raise DjangoValidationError({"detail": "User not found."})
        instance.full_clean()
        instance.save()
        return instance

    def delete(self, user_id: int) -> None:
        ok = self.repository.delete_user(user_id)
        if not ok:
            raise DjangoValidationError({"detail": "User not found."})

    def change_password(
        self,
        actor: CustomUser,
        target_user_id: int,
        *,
        old_password: Optional[str],
        new_password: str,
    ) -> CustomUser:
        user = self.repository.get_user_by_id(target_user_id)
        if not user:
            raise DjangoValidationError({"detail": "User not found."})

        is_admin = bool(actor.is_superuser or actor.is_staff)
        is_self = actor.pk == user.pk

        if not is_admin:
            if not is_self:
                raise DjangoValidationError({"detail": "You are not allowed to change this password."})
            if not old_password:
                raise DjangoValidationError({"old_password": "This field is required."})
            if not user.check_password(old_password):
                raise DjangoValidationError({"old_password": "Incorrect password."})

        if old_password and old_password == new_password:
            raise DjangoValidationError({"new_password": "New password must be different from old password."})

        user.set_password(new_password)
        user.save()
        return user
