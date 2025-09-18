# registrations/interfaces/registration_repository_interface.py
"""
Mantengo la interfaz del repositorio para desacoplar la capa de servicio del ORM.
De esta forma, si en el futuro cambio la implementación (por ejemplo, otro backend),
no impacto a los servicios ni a los controllers.
"""

from typing import Optional, Any, List, Dict
from abc import ABC, abstractmethod

# Importo desde el package para respetar la API pública del módulo de modelos
from registrations.models import Registration


class IRegistrationRepository(ABC):
    """
    Defino los contratos que debe cumplir cualquier repositorio de Registration.
    Incluyo operaciones de lectura, escritura y helpers de existencia para reglas
    de negocio, además del manejo de indisponibilidades (slots) asociado.
    """

    @abstractmethod
    def list(self, tournament_category_id: Optional[int] = None) -> Any:
        """
        Devuelvo un queryset/lista de registrations; si se pasa tournament_category_id,
        filtro por esa categoría. Prefiero devolver un QuerySet para permitir
        paginación y filtros en capas superiores.
        """
        pass

    @abstractmethod
    def get_by_id(self, reg_id: int) -> Optional[Registration]:
        """
        Obtengo una registration por id o None si no existe. Mantengo select_related
        y prefetch en la implementación concreta para evitar N+1.
        """
        pass

    @abstractmethod
    def exists_player_in_tc(self, tc_id: int, player_id: int) -> bool:
        """
        Verifico si el player ya está inscripto en la TournamentCategory tc_id.
        """
        pass

    @abstractmethod
    def exists_partner_in_tc(self, tc_id: int, partner_id: int) -> bool:
        """
        Verifico si el partner ya está inscripto en la TournamentCategory tc_id.
        """
        pass

    @abstractmethod
    def exists_pair_in_tc(self, tc_id: int, player_id: int, partner_id: int) -> bool:
        """
        Verifico si la pareja (player, partner) ya existe en la misma TournamentCategory,
        contemplando el orden inverso (player<->partner).
        """
        pass

    @abstractmethod
    def create(self, **data) -> Registration:
        """
        Creo y retorno la Registration. La validación de dominio corre en el service
        y la limpieza a nivel modelo (full_clean) se ejecuta antes de persistir.
        """
        pass

    @abstractmethod
    def delete(self, instance: Registration) -> None:
        """
        Elimino la Registration. Si en el futuro aplico soft-delete, el cambio queda
        encapsulado en la implementación concreta sin impactar al resto.
        """
        pass

    # ---------- Indisponibilidades (slots) ----------
    @abstractmethod
    def add_unavailability(self, registration: Registration, slots: List[Dict[str, Any]]) -> None:
        """
        Inserto en bloque los slots de indisponibilidad asociados a una inscripción.
        Formato de cada slot: {"day_of_week": int, "start_time": time, "end_time": time}
        La implementación concreta debe usar transacciones y bulk_create para eficiencia.
        """
        pass
