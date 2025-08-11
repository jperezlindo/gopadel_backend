from typing import Optional
from users.models.user import CustomUser
from users.interfaces.user_repository_interface import UserRepositoryInterface
from users.repositories.user_repository import UserRepository
from users.schemas.user_serializer import UserSerializer
from users.exceptions import UserNotFoundException
from rest_framework.exceptions import PermissionDenied, ValidationError, NotFound


class UserService:
    def __init__(self, user_repository: UserRepositoryInterface = UserRepository()):
        self.user_repository = user_repository

    def list_users(self):
        users = self.user_repository.get_all_users()
        return UserSerializer(users, many=True).data

    def retrieve_user(self, user_id: int):
        user = self.user_repository.get_user_by_id(user_id)
        if user is None:
            raise UserNotFoundException(f"User with ID {user_id} not found.")
        return UserSerializer(user).data

    def create_user(self, data: dict):
        user = self.user_repository.create_user(data)
        return UserSerializer(user).data

    def update_user(self, user_id: int, data: dict):
        user = self.user_repository.update_user(user_id, data)
        if user is None:
            raise UserNotFoundException(f"User with ID {user_id} not found.")
        return UserSerializer(user).data

    def delete_user(self, user_id: int):
        user = self.user_repository.delete_user(user_id)
        if user is None:
            raise UserNotFoundException(f"User with ID {user_id} not found.")
        return UserSerializer(user).data
    
    def change_password(
            self,
            actor: CustomUser,
            target_user_id: int,
            *,
            old_password: Optional[str],
            new_password: str,
        ) -> CustomUser:
            user = self.user_repository.get_user_by_id(target_user_id)
            if not user:
                raise NotFound("User not found")

            is_admin = bool(actor.is_superuser or actor.is_staff)
            is_self = actor.pk == user.pk

            if not is_admin:
                if not is_self:
                    raise PermissionDenied("You cannot change another user's password.")
                if not old_password:
                    raise ValidationError({"old_password": "This field is required."})
                if not user.check_password(old_password):
                    raise ValidationError({"old_password": "Incorrect password."})

            if old_password and old_password == new_password:
                raise ValidationError({"new_password": "New password must be different from old password."})

            user.set_password(new_password)
            user.save()
            return user