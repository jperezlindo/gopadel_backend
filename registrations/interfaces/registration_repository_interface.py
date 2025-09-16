from typing import Optional, Any
from abc import ABC, abstractmethod
from registrations.models.registration import Registration

class IRegistrationRepository(ABC):
    @abstractmethod
    def list(self, tournament_category_id: Optional[int] = None) -> Any:
        pass

    @abstractmethod
    def get_by_id(self, reg_id: int) -> Optional[Registration]:
        pass

    @abstractmethod
    def exists_player_in_tc(self, tc_id: int, player_id: int) -> bool:
        pass

    @abstractmethod
    def exists_partner_in_tc(self, tc_id: int, partner_id: int) -> bool:
        pass

    @abstractmethod
    def exists_pair_in_tc(self, tc_id: int, player_id: int, partner_id: int) -> bool:
        pass

    @abstractmethod
    def create(self, **data) -> Registration:
        pass

    @abstractmethod
    def delete(self, instance: Registration) -> None:
        pass

