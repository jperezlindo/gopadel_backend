# categories/controllers/category_controller.py
from typing import Optional

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny  # Permito acceso público por ahora (solo lectura).
from rest_framework import status

from categories.services.category_service import CategoryService
from categories.schemas.category_serializers import CategoryReadSerializer
from utils.pagination import DefaultPagination
from utils.response_handler import success_response


def _parse_bool(value: Optional[str]) -> Optional[bool]:
    """
    Convierto valores de query string a booleano real:
    - true/1/yes/sí -> True
    - false/0/no -> False
    - None o cualquier cosa inválida -> None (no aplico filtro)
    """
    if value is None:
        return None
    v = value.strip().lower()
    if v in {"1", "true", "t", "yes", "y", "si", "sí"}:
        return True
    if v in {"0", "false", "f", "no", "n"}:
        return False
    return None  # inválido => ignoro filtro


class CategoryListView(APIView):
    """
    GET /api/v1/categories/?is_active=true&search=pre&order_by=name

    Decisiones:
    - Mantengo el controller fino: parseo inputs, delego negocio al service, serializo.
    - Uso nuestra paginación DefaultPagination para responder con:
      {count, page, page_size, total_pages, next, previous, results}
    - Dejo el acceso abierto (AllowAny) ya que es lectura pública por ahora.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        # 1) Parseo filtros desde query string
        is_active = _parse_bool(request.query_params.get("is_active"))
        search = request.query_params.get("search")
        order_by = request.query_params.get("order_by")

        # 2) Llamo al service (reglas/validaciones viven ahí)
        service = CategoryService()
        qs = service.list_categories(is_active=is_active, search=search, order_by=order_by)

        # 3) Aplico paginación DRF unificada
        paginator = DefaultPagination()
        page = paginator.paginate_queryset(qs, request)

        # 4) Serializo la página resultante (many=True)
        serializer = CategoryReadSerializer(page, many=True)

        # 5) Devuelvo la respuesta paginada con el contrato estándar de paginación
        return paginator.get_paginated_response(serializer.data)


class CategoryDetailView(APIView):
    """
    GET /api/v1/categories/<id>/

    Decisiones:
    - Dejo que el service levante ValidationError(code='not_found') si no existe.
    - No capturo la excepción aquí: nuestro custom_exception_handler la mapea a 404 con payload consistente.
    - Para éxito, uso success_response para mantener formato uniforme.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, pk: int):
        service = CategoryService()
        category = service.get_category(pk)  # Si no existe, el handler devolverá 404 automáticamente.
        data = CategoryReadSerializer(category).data
        return success_response(data, status.HTTP_200_OK)
