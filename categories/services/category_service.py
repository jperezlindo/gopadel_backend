# categories/services/category_service.py
from typing import Optional
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from categories.models.category import Category
from categories.repositories.category_repository import CategoryRepository


class CategoryService:
    """
    Servicio de dominio para Categories.

    Objetivo del service:
    - Centralizar reglas de negocio y validaciones previas a tocar la base de datos.
    - Proveer una API estable a los controllers para que no dependan del ORM.
    - Dejar preparado el punto único donde voy a añadir validaciones más complejas
      cuando habilitemos creación, edición o lógica adicional.
    """

    def __init__(self, repo: Optional[CategoryRepository] = None) -> None:
        # Inyecto el repositorio para favorecer testeo y desacoplar esta capa del ORM.
        # Si no me pasan uno (tests/mocks), uso el repo real por defecto.
        self.repo = repo or CategoryRepository()

    def list_categories(
        self,
        *,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        order_by: Optional[str] = None,
    ) -> QuerySet[Category]:
        """
        Devuelvo un QuerySet filtrado y ordenado de categorías.

        Por qué devuelvo QuerySet y no una lista:
        - El controller usa la paginación de DRF que trabaja sobre QuerySet de forma eficiente.
        - Evito materializar todo en memoria si hay muchos registros.
        - Mantengo lazy evaluation y dejo que la capa de presentación decida cuándo evaluar.

        Parámetros:
        - is_active: si viene, filtro por estado exacto (True/False).
        - search: match por nombre con icontains (búsqueda parcial y case-insensitive).
        - order_by: dejo ordenar por un subconjunto permitido que define el repositorio
                    para evitar inyección de campos arbitrarios.

        Flujo:
        - El service no reimplementa filtros; delega al repo para mantener una sola fuente de verdad.
        """
        return self.repo.list(is_active=is_active, search=search, order_by=order_by)

    def get_category(self, pk: int) -> Category:
        """
        Obtengo una categoría por su PK.

        Comportamiento ante no encontrado:
        - Si el repo devuelve None, levanto un ValidationError con code='not_found'.
        - Nuestro custom_exception_handler mapea ese código a HTTP 404 automáticamente.
        - Esto mantiene consistente la forma en que comunicamos "no encontrado" al front.

        Nota:
        - Prefiero usar ValidationError con code específico en lugar de lanzar NotFound
          directamente aquí, porque centralizamos el formateo en el handler y mantenemos
          un único contrato de errores para toda la API.
        """
        item = self.repo.get_by_id(pk)
        if not item:
            # El code='not_found' es clave para que el handler lo convierta en 404.
            raise ValidationError("Category not found", code="not_found")
        return item
