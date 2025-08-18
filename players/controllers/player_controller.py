from typing import Any
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError

from players.services.player_service import PlayerService
from players.schemas.player_serializer import (
    PlayerSerializer,
    CreatePlayerSerializer,
    UpdatePlayerSerializer
)

from utils.response_handler import success_response, error_response

class PlayerListCreateView(APIView):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.player_service = PlayerService()

    def get(self, request) -> Response:
        try:
            players = self.player_service.list()
            data = PlayerSerializer(players, many=True).data
            return success_response(data, status.HTTP_200_OK)
        except Exception as e:
            return error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request) -> Response:
        try:
            serializer = CreatePlayerSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            player = self.player_service.create(serializer.validated_data) # type: ignore
            data = PlayerSerializer(player).data
            return success_response(data, status.HTTP_201_CREATED)
        except ValidationError as e:
            payload = getattr(e, "message_dict", {"detail": str(e)})
            return error_response(payload, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)

class PlayerDetailView(APIView):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.player_service = PlayerService()

    def get(self, request, player_id: int) -> Response:
        try:
            player = self.player_service.get(player_id)
            data = PlayerSerializer(player).data
            return success_response(data, status.HTTP_200_OK)
        except ValidationError:
            return error_response({"detail": "Player not found."}, status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, pk: int) -> Response:
        return self._update(request, pk, partial=False)

    def patch(self, request, pk: int) -> Response:
        return self._update(request, pk, partial=True)

    def _update(self, request, player_id: int, partial: bool) -> Response:
        try:
            instance = self.player_service.get(player_id)
        except ValidationError:
            return error_response({"detail": "Player not found."}, status.HTTP_404_NOT_FOUND)

        serializer = UpdatePlayerSerializer(instance, data=request.data, partial=partial)
        try:
            serializer.is_valid(raise_exception=True)
            player = self.player_service.update(player_id, serializer.validated_data) # type: ignore
            data = PlayerSerializer(player).data
            return success_response(data, status.HTTP_200_OK)
        except ValidationError as e:
            payload = getattr(e, "message_dict", {"detail": str(e)})
            return error_response(payload, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, player_id: int) -> Response:
        try:
            self.player_service.delete(player_id)
            return success_response({"detail": "Player deleted successfully"}, status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)
