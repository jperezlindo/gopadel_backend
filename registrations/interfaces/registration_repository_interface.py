from typing import Any, Optional
from abc import ABC, abstractmethod
from registrations.models.registration import Registration


class RegistrationRepositoryInterface(ABC):
    @abstractmethod
    def list(self, **filters) -> Any:
        pass

    @abstractmethod
    def get_by_id(self, reg_id: int) -> Optional[Registration]:
        pass

    @abstractmethod
    def create(self, data: dict) -> Registration:
        pass

    @abstractmethod
    def update(self, instance: Registration, data: dict) -> Registration:
        pass

    @abstractmethod
    def delete(self, instance: Registration) -> None:
        pass

    @abstractmethod
    def exists_person_in_tournament(self, person_id: int, tournament_id: int) -> bool:
        pass

