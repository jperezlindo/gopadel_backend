# users/interfaces/user_repository_interface.py
from typing import Any, Optional
from abc import ABC, abstractmethod
from users.models.user import CustomUser

class UserRepositoryInterface(ABC):
    """
    Defino la interfaz del repositorio de usuarios para desacoplar
    las capas superiores (services/controllers) del ORM concreto.
    Esto facilita tests (mocks/fakes) y futuras migraciones de persistencia.
    """

    @abstractmethod
    def get_all_users(self) -> Any:
        """
        Devuelve un QuerySet (o iterable) con los usuarios visibles en UI.
        La implementación puede filtrar activos/no eliminados/no superusers.
        """
        raise NotImplementedError

    @abstractmethod
    def get_user_by_id(self, user_id: int) -> Optional[CustomUser]:
        """
        Devuelve una instancia de CustomUser o None si no existe.
        La implementación puede respetar soft-delete (excluir is_deleted=True).
        """
        raise NotImplementedError

    @abstractmethod
    def create_user(self, data: dict) -> CustomUser:
        """
        Crea un usuario. La implementación debería delegar en el manager
        para hashear password y aplicar defaults coherentes.
        """
        raise NotImplementedError

    @abstractmethod
    def update_user(self, user_id: int, data: dict) -> Optional[CustomUser]:
        """
        Actualiza campos simples del usuario. Debe retornar la instancia actualizada
        o None si el usuario no existe. No debe modificar el password.
        """
        raise NotImplementedError

    @abstractmethod
    def delete_user(self, user_id: int) -> bool:
        """
        Realiza un soft-delete (is_deleted=True) y desactiva (is_active=False).
        Retorna True si se aplicó el cambio, False si el usuario no existía.
        """
        raise NotImplementedError
