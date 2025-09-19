# categories/services/category_service.py
from typing import Optional, Dict, Any
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import QuerySet

from categories.models.category import Category
from categories.repositories.category_repository import CategoryRepository


class CategoryService:
    """
    Servicio de dominio para Categories.

    Yo centralizo acá las reglas de negocio:
    - Valido y normalizo inputs (p. ej., name sin espacios).
    - Llamo al repo para persistencia/lectura (una sola fuente de verdad).
    - Lanzo ValidationError con code='not_found' cuando corresponde, porque
      mi custom_exception_handler lo mapea a HTTP 404.
    """

    def __init__(self, repo: Optional[CategoryRepository] = None) -> None:
        # Inyecto el repositorio para testear fácil; por defecto uso el real.
        self.repo = repo or CategoryRepository()

    # =========================
    # Lectura
    # =========================
    def list_categories(
        self,
        *,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        order_by: Optional[str] = None,
    ) -> QuerySet[Category]:
        """
        Devuelvo un QuerySet filtrado y ordenado. Mantengo lazy evaluation
        porque la paginación de DRF trabaja mejor con QuerySets.
        """
        return self.repo.list(is_active=is_active, search=search, order_by=order_by)

    def get_category(self, pk: int) -> Category:
        """
        Obtengo una categoría por PK. Si no existe, levanto ValidationError con
        code='not_found' para que el handler lo convierta en 404.
        """
        item = self.repo.get_by_id(pk)
        if not item:
            raise ValidationError("Category not found", code="not_found")
        return item

    # =========================
    # Escritura
    # =========================
    def _normalize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Yo normalizo campos comunes acá para no repetir en create/update.
        - 'name': le hago strip si viene.
        """
        data = dict(payload) if payload else {}
        if "name" in data and data["name"] is not None:
            data["name"] = str(data["name"]).strip()
        return data

    def create_category(self, payload: Dict[str, Any]) -> Category:
        """
        Creo una categoría. Valido dominio con full_clean() antes de persistir.
        - Si falta 'name' o viene vacío, full_clean() fallará si el modelo lo exige.
        - Si hay unicidad a nivel DB (name único), capturo IntegrityError y lo traduzco.
        """
        data = self._normalize_payload(payload)

        # Prevalido con un objeto temporal para ejecutar full_clean() sin tocar DB.
        candidate = Category(**{k: v for k, v in data.items() if k in {f.name for f in Category._meta.fields}})
        candidate.full_clean()  # levanta ValidationError si hay problemas de dominio

        try:
            return self.repo.create(data)
        except IntegrityError as e:
            # Traduzco conflictos comunes a un mensaje consistente.
            msg = str(e).lower()
            if "unique" in msg and "name" in msg:
                raise ValidationError({"name": ["Category name must be unique."]})
            raise

    def update_category(self, pk: int, payload: Dict[str, Any]) -> Category:
        """
        Actualizo parcialmente una categoría. Aplico solo campos presentes.
        - 404 si no existe.
        - Valido con full_clean() antes de guardar.
        """
        instance = self.repo.get_by_id(pk)
        if not instance:
            raise ValidationError("Category not found", code="not_found")

        data = self._normalize_payload(payload)

        # Aplico solo claves conocidas del modelo (evito campos basura).
        for field in {f.name for f in Category._meta.fields}:
            if field in data and data[field] is not None:
                setattr(instance, field, data[field])
            # Si quisieras permitir setear None explícito para campos nullables,
            # podés manejarlo acá (ej.: if field in data: setattr(...)).

        # Valido antes de persistir
        instance.full_clean()

        try:
            return self.repo.save(instance)
        except IntegrityError as e:
            msg = str(e).lower()
            if "unique" in msg and "name" in msg:
                raise ValidationError({"name": ["Category name must be unique."]})
            raise

    def delete_category(self, pk: int) -> None:
        """
        Borro la categoría. Si no existe, devuelvo 404 via ValidationError(not_found).
        """
        instance = self.repo.get_by_id(pk)
        if not instance:
            raise ValidationError("Category not found", code="not_found")
        self.repo.delete(instance)
