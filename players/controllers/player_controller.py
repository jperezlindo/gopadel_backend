# players/controllers/player_controller.py
from typing import Any, Dict, Optional, cast

from django.core.exceptions import ValidationError as DjangoVE
from rest_framework import permissions, status
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import OpenApiParameter, extend_schema

from players.schemas.player_serializer import (
    CreatePlayerSerializer,
    PlayerSearchSerializer,
    PlayerSerializer,
    UpdatePlayerSerializer,
)
from players.services.player_service import PlayerService
from utils.error_mapper import map_validation_error_status
from utils.pagination import DefaultPagination
from utils.response_handler import error_response, success_response


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


class PlayerListCreateView(APIView):
    """
    Listado paginado y creación de jugadores.
    Decisiones:
    - GET: uso DefaultPagination para devolver count, page, page_size, total_pages, results.
    - POST: valido con CreatePlayerSerializer y delego a PlayerService.
    """
    permission_classes = [permissions.IsAuthenticated]

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.player_service = PlayerService()
        self.paginator = DefaultPagination()

    @extend_schema(
        summary="List players",
        responses={200: PlayerSerializer(many=True)},
    )
    def get(self, request) -> Response:
        try:
            queryset = self.player_service.list()
            page = self.paginator.paginate_queryset(queryset, request, view=self)
            data = PlayerSerializer(page, many=True).data
            paginated = self.paginator.get_paginated_response(data)
            # success_response no re-envuelve; mando directamente el payload paginado.
            return success_response(paginated.data, status.HTTP_200_OK)
        except Exception:
            return error_response({"detail": ["Internal server error"]}, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        summary="Create player",
        request=CreatePlayerSerializer,
        responses={201: PlayerSerializer},
    )
    def post(self, request) -> Response:
        try:
            serializer = CreatePlayerSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data: Dict[str, Any] = cast(Dict[str, Any], serializer.validated_data)
            player = self.player_service.create(data)
            return success_response(PlayerSerializer(player).data, status.HTTP_201_CREATED)

        except DRFValidationError as exc:
            return error_response(normalize_errors(getattr(exc, "detail", str(exc))), status.HTTP_400_BAD_REQUEST)
        except DjangoVE as exc:
            http_status = map_validation_error_status(exc)
            payload = getattr(exc, "message_dict", None) or getattr(exc, "messages", None) or str(exc)
            return error_response(normalize_errors(payload), http_status)
        except Exception:
            return error_response({"detail": ["Internal server error"]}, status.HTTP_500_INTERNAL_SERVER_ERROR)


class PlayerDetailView(APIView):
    """
    Detalle, actualización y borrado de un jugador.
    - GET    /players/<id>/
    - PUT    /players/<id>/
    - PATCH  /players/<id>/
    - DELETE /players/<id>/
    Nota: el borrado es FÍSICO (modelo sin is_deleted).
    """
    permission_classes = [permissions.IsAuthenticated]

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.player_service = PlayerService()

    @extend_schema(
        summary="Get player by ID",
        responses={200: PlayerSerializer},
    )
    def get(self, request, player_id: int) -> Response:
        try:
            player = self.player_service.get(player_id)
            return success_response(PlayerSerializer(player).data, status.HTTP_200_OK)
        except DjangoVE as exc:
            http_status = map_validation_error_status(exc)
            payload = getattr(exc, "message_dict", None) or getattr(exc, "messages", None) or str(exc)
            return error_response(normalize_errors(payload), http_status)
        except Exception:
            return error_response({"detail": ["Internal server error"]}, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        summary="Update player (PUT)",
        request=UpdatePlayerSerializer,
        responses={200: PlayerSerializer},
    )
    def put(self, request, player_id: int) -> Response:
        return self._update(request, player_id, partial=False)

    @extend_schema(
        summary="Partial update player (PATCH)",
        request=UpdatePlayerSerializer,
        responses={200: PlayerSerializer},
    )
    def patch(self, request, player_id: int) -> Response:
        return self._update(request, player_id, partial=True)

    def _update(self, request, player_id: int, partial: bool) -> Response:
        try:
            serializer = UpdatePlayerSerializer(data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            data: Dict[str, Any] = cast(Dict[str, Any], serializer.validated_data)
            player = self.player_service.update(player_id, data)
            return success_response(PlayerSerializer(player).data, status.HTTP_200_OK)

        except DRFValidationError as exc:
            return error_response(normalize_errors(getattr(exc, "detail", str(exc))), status.HTTP_400_BAD_REQUEST)
        except DjangoVE as exc:
            http_status = map_validation_error_status(exc)
            payload = getattr(exc, "message_dict", None) or getattr(exc, "messages", None) or str(exc)
            return error_response(normalize_errors(payload), http_status)
        except Exception:
            return error_response({"detail": ["Internal server error"]}, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        summary="Delete player",
        responses={204: None},
    )
    def delete(self, request, player_id: int) -> Response:
        try:
            self.player_service.delete(player_id)
            # 204 No Content => no body
            return Response(status=status.HTTP_204_NO_CONTENT)
        except DjangoVE as exc:
            http_status = map_validation_error_status(exc)
            payload = getattr(exc, "message_dict", None) or getattr(exc, "messages", None) or str(exc)
            return error_response(normalize_errors(payload), http_status)
        except Exception:
            return error_response({"detail": ["Internal server error"]}, status.HTTP_500_INTERNAL_SERVER_ERROR)


class PlayerSearchView(APIView):
    """
    Búsqueda de jugadores:
      GET /api/v1/players/search/?q=texto&limit=50
    Busca por:
      - Player.nick_name (icontains)
      - users.CustomUser.name / last_name / email (icontains) vía Player.user
    """
    permission_classes = [permissions.IsAuthenticated]  # cambiar a AllowAny si lo necesitás público

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.player_service = PlayerService()

    @extend_schema(
        summary="Search players by nick_name or user fields",
        parameters=[
            OpenApiParameter(name="q", description="Texto a buscar (mín. 2 caracteres)", required=False, type=str),
            OpenApiParameter(name="limit", description="Cantidad máxima (1-200)", required=False, type=int),
        ],
        responses={200: PlayerSearchSerializer(many=True)},
    )
    def get(self, request) -> Response:
        q = request.query_params.get("q") or request.query_params.get("nick") or ""
        limit_raw: Optional[str] = request.query_params.get("limit")

        try:
            limit: Optional[int] = int(limit_raw) if limit_raw is not None else 50
        except (TypeError, ValueError):
            limit = 50

        try:
            players_qs = self.player_service.search(q, limit=limit)
            data = PlayerSearchSerializer(players_qs, many=True).data
            return success_response(data, status.HTTP_200_OK)
        except DjangoVE as exc:
            http_status = map_validation_error_status(exc)
            payload = getattr(exc, "message_dict", None) or getattr(exc, "messages", None) or str(exc)
            return error_response(normalize_errors(payload), http_status)
        except Exception:
            return error_response({"detail": ["Internal server error"]}, status.HTTP_500_INTERNAL_SERVER_ERROR)
