# cities/repositories/city_repository.py
from typing import Iterable, Optional
from django.db.models import Q, QuerySet
from cities.models import City


class CityRepository:
    """
    Centralizo acceso al ORM de City.
    Decisiones:
    - Oculto soft-deleted por defecto (is_deleted=False).
    - Expondo helpers de listado/búsqueda y cambios de estado.
    """

    def _base_qs(self) -> QuerySet:
        return City.objects.filter(is_deleted=False)

    def _base_qs_including_deleted(self) -> QuerySet:
        return City.objects.all()

    # -------- Listado / búsqueda --------
    def list(
        self,
        *,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        include_deleted: bool = False,
        ordering: Optional[Iterable[str]] = None,
    ) -> QuerySet:
        qs = self._base_qs_including_deleted() if include_deleted else self._base_qs()

        if is_active is not None:
            qs = qs.filter(is_active=is_active)

        if search:
            s = search.strip()
            if s:
                qs = qs.filter(
                    Q(name__icontains=s) |
                    Q(cod__icontains=s)
                )

        if ordering:
            qs = qs.order_by(*ordering)

        return qs

    # -------- Obtención puntual --------
    def get_by_id(self, city_id: int, *, include_deleted: bool = False) -> Optional[City]:
        qs = self._base_qs_including_deleted() if include_deleted else self._base_qs()
        return qs.filter(pk=city_id).first()

    def get_by_cod(self, cod: str, *, include_deleted: bool = False) -> Optional[City]:
        code = (cod or "").strip().upper()
        qs = self._base_qs_including_deleted() if include_deleted else self._base_qs()
        return qs.filter(cod__iexact=code).first()

    # -------- Escritura --------
    def create(self, data: dict) -> City:
        return City.objects.create(**data)

    def update(self, instance: City, data: dict) -> City:
        for k, v in data.items():
            setattr(instance, k, v)
        instance.save()
        return instance

    # -------- Cambios de estado --------
    def soft_delete(self, instance: City) -> City:
        instance.is_deleted = True
        instance.is_active = False
        instance.save(update_fields=["is_deleted", "is_active", "updated_at"])
        return instance

    def restore(self, instance: City) -> City:
        instance.is_deleted = False
        instance.save(update_fields=["is_deleted", "updated_at"])
        return instance
