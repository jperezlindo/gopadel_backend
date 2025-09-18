# roles/controllers/rol_controller.py
from typing import Any, Optional

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from roles.repositories.rol_repository import RolRepository
from roles.schemas.rol_serializer import RolSerializer
from utils.pagination import DefaultPagination
from utils.response_handler import success_response, error_response


class RolListView(APIView):
    """
    Expongo el listado de roles del sistema en modo solo lectura.
    Decisiones:
    - Los roles son predefinidos (ADMIN, EMPLOYEE, PLAYER), por lo que no se permite crear/editar/borrar.
    - Se agrega paginación unificada (DefaultPagination) para mantener contrato estable con el front.
    - Permito filtrar por `is_active=true|false` y buscar por nombre con `search`.
    - Permito `ordering` opcional (por defecto el modelo ya ordena por name).
    """

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.repo = RolRepository()
        self.paginator = DefaultPagination()

    def get(self, request) -> Response:
        try:
            # Filtros básicos por query params
            include_inactive = request.query_params.get("include_inactive")
            only_active = request.query_params.get("is_active")  # "true" / "false" / None
            search = request.query_params.get("search", "")
            ordering = request.query_params.getlist("ordering") or None

            # Si viene is_active, se respeta ese filtro; si no, se puede usar include_inactive
            if only_active is not None:
                is_active = only_active.strip().lower() in ("1", "true", "yes")
                qs = self.repo.list_all(include_inactive=True, ordering=ordering).filter(is_active=is_active)
            else:
                inc_inactive = (include_inactive or "").strip().lower() in ("1", "true", "yes")
                qs = self.repo.list_all(include_inactive=inc_inactive, ordering=ordering)

            # Búsqueda por nombre (icontains)
            if search:
                s = search.strip()
                if s:
                    qs = qs.filter(name__icontains=s)

            # Paginación y serialización
            page = self.paginator.paginate_queryset(qs, request, view=self)
            data = RolSerializer(page, many=True).data
            paginated = self.paginator.get_paginated_response(data)
            return success_response(paginated.data, status.HTTP_200_OK)

        except Exception:
            # Se devuelve 500 con mensaje uniforme para no filtrar detalles sensibles.
            return error_response({"detail": ["Internal server error"]}, status.HTTP_500_INTERNAL_SERVER_ERROR)


class RolDetailView(APIView):
    """
    Expongo detalle de un rol por id, en modo solo lectura.
    Si el rol no existe (o está soft-deleted), se devuelve 404.
    """

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.repo = RolRepository()

    def get(self, request, pk: int) -> Response:
        try:
            instance = self.repo.get_by_id(pk)
            if not instance:
                return error_response({"detail": ["Role not found."]}, status.HTTP_404_NOT_FOUND)
            data = RolSerializer(instance).data
            return success_response(data, status.HTTP_200_OK)
        except Exception:
            return error_response({"detail": ["Internal server error"]}, status.HTTP_500_INTERNAL_SERVER_ERROR)
