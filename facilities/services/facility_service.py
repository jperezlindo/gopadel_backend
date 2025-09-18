# facilities/services/facility_service.py
from typing import Any, Dict, Optional
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction

from facilities.models import Facility
from facilities.repositories.facility_repository import FacilityRepository


class FacilityService:
    """
    Orquesto reglas de negocio para Facilities:
    - Centralizo not_found con ValidationError(code="not_found") para que el handler lo mapee a 404.
    - Aseguro atomicidad en operaciones de escritura.
    """

    def __init__(self, repository: Optional[FacilityRepository] = None):
        self.repo = repository or FacilityRepository()

    # ------- Lectura -------
    def list(
        self, *,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        include_deleted: bool = False,
        ordering: Optional[list[str]] = None,
    ) -> Any:
        return self.repo.list(
            search=search,
            is_active=is_active,
            include_deleted=include_deleted,
            ordering=ordering,
        )

    def get(self, facility_id: int) -> Facility:
        inst = self.repo.get_by_id(facility_id)
        if not inst:
            raise DjangoValidationError({"detail": ["Facility not found."]}, code="not_found")
        return inst

    # ------- Escritura -------
    def create(self, data: Dict) -> Facility:
        with transaction.atomic():
            inst = self.repo.create(data)
            # full_clean se dispara en save() del modelo (override)
            return inst

    def update(self, facility_id: int, data: Dict) -> Facility:
        with transaction.atomic():
            inst = self.repo.get_by_id(facility_id)
            if not inst:
                raise DjangoValidationError({"detail": ["Facility not found."]}, code="not_found")
            inst = self.repo.update(inst, data)
            return inst

    def delete(self, facility_id: int) -> None:
        with transaction.atomic():
            inst = self.repo.get_by_id(facility_id)
            if not inst:
                raise DjangoValidationError({"detail": ["Facility not found."]}, code="not_found")
            self.repo.soft_delete(inst)
