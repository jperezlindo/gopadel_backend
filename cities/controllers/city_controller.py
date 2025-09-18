# cities/controllers/city_controller.py
from typing import Any, Optional

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from cities.services.city_service import CityService
from cities.schemas.city_serializer import (
    CitySerializer,
    CreateCitySerializer,
    UpdateCitySerializer,
)
from utils.pagination import DefaultPagination
from utils.response_handler import success_response, error_response


# -------- Normalizador local de errores (mismo contrato que en Users/Facilities) --------
def _as_list(val):
    if val is None:
        return []
    if isinstance(val, (list, tuple)):
        return [str(v) for v in val]
    return [str(val)]

def normalize_errors(err):
    if isinstance(err, dict):
        out = {}
        for k, v in err.items():
            out[str(k)] = _as_list(v)
        return out
    if isinstance(err, (list, tuple)):
        return {"non_field_errors": _as_list(err)}
    return {"detail": [str(err)]}


class CityListCreateView(APIView):
    """
    Listado paginado y creación de Cities.
    Filtros soportados: ?search=, ?is_active=true|false, ?include_deleted=true
    Orden: ?ordering=name&ordering=-created_at
    """

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.service = CityService()
        self.paginator = DefaultPagination()

    def get(self, request) -> Response:
        try:
            search = request.query_params.get("search")
            is_active_param = request.query_params.get("is_active")
            include_deleted = (request.query_params.get("include_deleted") or "").lower() in ("1", "true", "yes")
            ordering = request.query_params.getlist("ordering") or None

            is_active: Optional[bool] = None
            if is_active_param is not None:
                is_active = is_active_param.strip().lower() in ("1", "true", "yes")

            qs = self.service.list(
                search=search,
                is_active=is_active,
                include_deleted=include_deleted,
                ordering=ordering,
            )
            page = self.paginator.paginate_queryset(qs, request, view=self)
            data = CitySerializer(page, many=True).data
            paginated = self.paginator.get_paginated_response(data)
            return success_response(paginated.data, status.HTTP_200_OK)

        except Exception:
            return error_response({"detail": ["Internal server error"]}, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request) -> Response:
        try:
            serializer = CreateCitySerializer(data=request.data)
            if not serializer.is_valid():
                return error_response(normalize_errors(serializer.errors), status.HTTP_400_BAD_REQUEST)

            inst = self.service.create(serializer.validated_data)  # type: ignore
            data = CitySerializer(inst).data
            return success_response(data, status.HTTP_201_CREATED)

        except DjangoValidationError as e:
            payload = getattr(e, "message_dict", getattr(e, "messages", str(e)))
            return error_response(normalize_errors(payload), status.HTTP_400_BAD_REQUEST)
        except Exception:
            return error_response({"detail": ["Internal server error"]}, status.HTTP_500_INTERNAL_SERVER_ERROR)


class CityDetailView(APIView):
    """
    Detalle / actualización / borrado lógico de una City.
    - GET /cities/<id>/
    - PUT/PATCH /cities/<id>/
    - DELETE /cities/<id>/  (soft-delete: is_deleted=True, is_active=False)
    """

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.service = CityService()

    def get(self, request, pk: int) -> Response:
        try:
            inst = self.service.get(pk)
            return success_response(CitySerializer(inst).data, status.HTTP_200_OK)
        except DjangoValidationError:
            return error_response({"detail": ["City not found."]}, status.HTTP_404_NOT_FOUND)
        except Exception:
            return error_response({"detail": ["Internal server error"]}, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, pk: int) -> Response:
        return self._update(request, pk, partial=False)

    def patch(self, request, pk: int) -> Response:
        return self._update(request, pk, partial=True)

    def delete(self, request, pk: int) -> Response:
        try:
            self.service.delete(pk)
            return success_response({"message": "Deleted successfully"}, status.HTTP_200_OK)
        except DjangoValidationError:
            return error_response({"detail": ["City not found."]}, status.HTTP_404_NOT_FOUND)
        except Exception:
            return error_response({"detail": ["Internal server error"]}, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _update(self, request, pk: int, partial: bool) -> Response:
        try:
            current = self.service.get(pk)
        except DjangoValidationError:
            return error_response({"detail": ["City not found."]}, status.HTTP_404_NOT_FOUND)

        serializer = UpdateCitySerializer(current, data=request.data, partial=partial)
        try:
            if not serializer.is_valid():
                return error_response(normalize_errors(serializer.errors), status.HTTP_400_BAD_REQUEST)

            updated = self.service.update(pk, serializer.validated_data)  # type: ignore
            return success_response(CitySerializer(updated).data, status.HTTP_200_OK)

        except DjangoValidationError as e:
            payload = getattr(e, "message_dict", getattr(e, "messages", str(e)))
            return error_response(normalize_errors(payload), status.HTTP_400_BAD_REQUEST)
        except Exception:
            return error_response({"detail": ["Internal server error"]}, status.HTTP_500_INTERNAL_SERVER_ERROR)
