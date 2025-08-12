from typing import Any, Optional
from abc import ABC, abstractmethod
from users.models.user import CustomUser

class UserRepositoryInterface(ABC):

    @abstractmethod
    def get_all_users(self) -> Any:
        pass

    @abstractmethod
    def get_user_by_id(self, user_id: int) -> Optional[CustomUser]:
        pass

    @abstractmethod
    def create_user(self, data: dict) -> CustomUser:
        pass

    @abstractmethod
    def update_user(self, user_id: int, data: dict) -> Optional[CustomUser]:
        pass

    @abstractmethod
    def delete_user(self, user_id: int) -> bool:
        """Retorna True si realizó el borrado (soft), False si no existía."""
        pass
