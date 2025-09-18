# tournaments/controllers/tournament_controller.py
from typing import Any, Dict, Optional, cast

from django.core.exceptions import ValidationError as DjangoVE
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from tournaments.services.tournament_service import TournamentService
from tournaments.schemas.tournament_serializers import (
    CreateTournamentSerializer,
    TournamentSerializer,
    UpdateTournamentSerializer,
)
from utils.pagination import DefaultPagination
from utils.response_handler import error_response, success_response
from utils.error_mapper import map_validation_error_status


# ---------------- Helpers de normalización (contrato estable para UI) ----------------
def _as_list(val):
    if val is None:
        return []
    if isinstance(val, (list, tuple)):
        return [str(v) for v in val]
    return [str(val)]


def normalize_errors(err):
    """
    dict -> {campo: [msgs]}
    list/tuple -> {"non_field_errors": [...]}
    str -> {"detail": ["..."]}
    """
    if isinstance(err, dict):
        out = {}
        for k, v in err.items():
            out[str(k)] = _as_list(v)
        return out
    if isinstance(err, (list, tuple)):
        return {"non_field_errors": _as_list(err)}
    return {"detail": [str(err)]}


class TournamentListCreateView(APIView):
    """
    Listado paginado y creación de torneos.

    GET  /api/v1/tournaments/
      - Devuelve payload paginado (count, page, page_size, total_pages, results)
      - Incluye facility embebido y categorías vía prefetch (repo)

    POST /api/v1/tournaments/
      - Crea torneo y (opcional) categorías inline
    """

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.service = TournamentService()
        self.paginator = DefaultPagination()

    def get(self, request) -> Response:
        try:
            qs = self.service.list()
            page = self.paginator.paginate_queryset(qs, request, view=self)
            data = TournamentSerializer(page, many=True).data
            paginated = self.paginator.get_paginated_response(data)
            return success_response(paginated.data, status.HTTP_200_OK)
        except Exception:
            return error_response({"detail": ["Internal server error"]}, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request) -> Response:
        try:
            serializer = CreateTournamentSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance = self.service.create(cast(Dict[str, Any], serializer.validated_data))
            return success_response(TournamentSerializer(instance).data, status.HTTP_201_CREATED)

        except DjangoVE as exc:
            http_status = map_validation_error_status(exc)
            payload = getattr(exc, "message_dict", None) or getattr(exc, "messages", None) or str(exc)
            return error_response(normalize_errors(payload), http_status)
        except Exception:
            return error_response({"detail": ["Internal server error"]}, status.HTTP_500_INTERNAL_SERVER_ERROR)


class TournamentDetailView(APIView):
    """
    Detalle, actualización y borrado de un torneo.

    GET    /api/v1/tournaments/<pk>/
    PUT    /api/v1/tournaments/<pk>/
    PATCH  /api/v1/tournaments/<pk>/
    DELETE /api/v1/tournaments/<pk>/

    Nota:
    - Update soporta edición de categorías inline (service.update).
    - Borrado es FÍSICO y por cascada elimina sus categorías.
    """

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.service = TournamentService()

    def get(self, request, pk: int) -> Response:
        try:
            instance = self.service.get(pk)
            return success_response(TournamentSerializer(instance).data, status.HTTP_200_OK)

        except DjangoVE as exc:
            http_status = map_validation_error_status(exc)
            payload = getattr(exc, "message_dict", None) or getattr(exc, "messages", None) or str(exc)
            return error_response(normalize_errors(payload), http_status)
        except Exception:
            return error_response({"detail": ["Internal server error"]}, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, pk: int) -> Response:
        return self._update(request, pk, partial=False)

    def patch(self, request, pk: int) -> Response:
        return self._update(request, pk, partial=True)

    def _update(self, request, pk: int, partial: bool) -> Response:
        # Paso la instancia al serializer para validaciones coherentes (especialmente fechas en PATCH)
        try:
            current = self.service.get(pk)
        except DjangoVE as exc:
            http_status = map_validation_error_status(exc)
            payload = getattr(exc, "message_dict", None) or getattr(exc, "messages", None) or str(exc)
            return error_response(normalize_errors(payload), http_status)

        serializer = UpdateTournamentSerializer(current, data=request.data, partial=partial)
        try:
            serializer.is_valid(raise_exception=True)
            updated = self.service.update(pk, cast(Dict[str, Any], serializer.validated_data))
            return success_response(TournamentSerializer(updated).data, status.HTTP_200_OK)

        except DjangoVE as exc:
            http_status = map_validation_error_status(exc)
            payload = getattr(exc, "message_dict", None) or getattr(exc, "messages", None) or str(exc)
            return error_response(normalize_errors(payload), http_status)
        except Exception:
            return error_response({"detail": ["Internal server error"]}, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk: int) -> Response:
        try:
            self.service.delete(pk)
            # 204 No Content (más estándar para deletes)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except DjangoVE as exc:
            http_status = map_validation_error_status(exc)
            payload = getattr(exc, "message_dict", None) or getattr(exc, "messages", None) or str(exc)
            return error_response(normalize_errors(payload), http_status)
        except Exception:
            return error_response({"detail": ["Internal server error"]}, status.HTTP_500_INTERNAL_SERVER_ERROR)
