# cities/services/city_service.py
from typing import Any, Dict, Optional
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction

from cities.models import City
from cities.repositories.city_repository import CityRepository


class CityService:
    """
    Orquesto reglas de negocio para Cities:
    - Uso ValidationError(code="not_found") para mapear 404 vía handler.
    - Atomicidad garantizada en operaciones de escritura.
    """

    def __init__(self, repository: Optional[CityRepository] = None):
        self.repo = repository or CityRepository()

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

    def get(self, city_id: int) -> City:
        inst = self.repo.get_by_id(city_id)
        if not inst:
            raise DjangoValidationError({"detail": ["City not found."]}, code="not_found")
        return inst

    # ------- Escritura -------
    def create(self, data: Dict) -> City:
        with transaction.atomic():
            inst = self.repo.create(data)
            return inst

    def update(self, city_id: int, data: Dict) -> City:
        with transaction.atomic():
            inst = self.repo.get_by_id(city_id)
            if not inst:
                raise DjangoValidationError({"detail": ["City not found."]}, code="not_found")
            inst = self.repo.update(inst, data)
            return inst

    def delete(self, city_id: int) -> None:
        with transaction.atomic():
            inst = self.repo.get_by_id(city_id)
            if not inst:
                raise DjangoValidationError({"detail": ["City not found."]}, code="not_found")
            self.repo.soft_delete(inst)
