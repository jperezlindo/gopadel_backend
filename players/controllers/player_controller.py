# players/controllers/player_controller.py
from typing import Any, Dict, cast, Optional
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.core.exceptions import ValidationError as DjangoVE

from drf_spectacular.utils import extend_schema, OpenApiParameter

from players.services.player_service import PlayerService
from players.schemas.player_serializer import (
    PlayerSerializer,
    CreatePlayerSerializer,
    UpdatePlayerSerializer,
    PlayerSearchSerializer,
)

from utils.response_handler import success_response, error_response
from utils.error_mapper import map_validation_error_status


class PlayerListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.player_service = PlayerService()

    @extend_schema(
        summary="List players",
        responses={200: PlayerSerializer(many=True)},
    )
    def get(self, request) -> Response:
        try:
            players = self.player_service.list()
            data = PlayerSerializer(players, many=True).data
            return success_response(data, status.HTTP_200_OK)
        except Exception as e:
            return error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)

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
            return error_response(exc.detail, status.HTTP_400_BAD_REQUEST)
        except DjangoVE as exc:
            http_status = map_validation_error_status(exc)
            payload = getattr(exc, "message_dict", None) or getattr(exc, "messages", None) or str(exc)
            return error_response(payload, http_status)
        except Exception as e:
            return error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)


class PlayerDetailView(APIView):
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
            data = PlayerSerializer(player).data
            return success_response(data, status.HTTP_200_OK)
        except DjangoVE as exc:
            http_status = map_validation_error_status(exc)
            payload = getattr(exc, "message_dict", None) or getattr(exc, "messages", None) or str(exc)
            return error_response(payload, http_status)

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
            return error_response(exc.detail, status.HTTP_400_BAD_REQUEST)
        except DjangoVE as exc:
            http_status = map_validation_error_status(exc)
            payload = getattr(exc, "message_dict", None) or getattr(exc, "messages", None) or str(exc)
            return error_response(payload, http_status)
        except Exception:
            return error_response("Internal server error", status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        summary="Delete player",
        responses={204: None},
    )
    def delete(self, request, player_id: int) -> Response:
        try:
            self.player_service.delete(player_id)
            return success_response({"detail": "Player deleted successfully"}, status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)


class PlayerSearchView(APIView):
    """
    GET /api/v1/players/search/?q=texto&limit=50
    Busca por:
      - Player.nick_name (icontains)
      - users.CustomUser.name / last_name / email (icontains) vía Player.user
    """
    permission_classes = [permissions.IsAuthenticated]  # cambia a AllowAny si querés público

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.player_service = PlayerService()

    @extend_schema(
        summary="Search players by nick_name or user fields",
        parameters=[
            OpenApiParameter(name="q", description="Texto a buscar", required=False, type=str),
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
            return error_response(payload, http_status)
        except Exception as e:
            return error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)
