# tournaments/controllers/tournament_controller.py
from typing import Any
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError

from tournaments.services.tournament_service import TournamentService
from tournaments.schemas.tournament_serializers import (
    TournamentSerializer,
    CreateTournamentSerializer,
    UpdateTournamentSerializer,
)
from utils.response_handler import success_response, error_response


class TournamentListCreateView(APIView):
    """
    GET  /api/v1/tournaments/     -> Lista torneos (incluye categories via prefetch)
    POST /api/v1/tournaments/     -> Crea torneo + categories inline (service.create)
    """
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.service = TournamentService()

    def get(self, request) -> Response:
        try:
            items = self.service.list()
            data = TournamentSerializer(items, many=True).data
            return success_response(data, status.HTTP_200_OK)
        except Exception:
            return error_response("Internal server error", status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request) -> Response:
        try:
            serializer = CreateTournamentSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance = self.service.create(serializer.validated_data)  # type: ignore
            data = TournamentSerializer(instance).data
            return success_response(data, status.HTTP_201_CREATED)
        except ValidationError as e:
            payload = getattr(e, "message_dict", {"detail": str(e)})
            return error_response(payload, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print("Error en TournamentListCreateView.post:", e)
            return error_response("Internal server error", status.HTTP_500_INTERNAL_SERVER_ERROR)


class TournamentDetailView(APIView):
    """
    GET    /api/v1/tournaments/<pk>/
    PUT    /api/v1/tournaments/<pk>/
    PATCH  /api/v1/tournaments/<pk>/
    DELETE /api/v1/tournaments/<pk>/
    * Update NO toca categories por ahora (solo campos del torneo).
    """
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.service = TournamentService()

    def get(self, request, pk: int) -> Response:
        try:
            instance = self.service.get(pk)
            data = TournamentSerializer(instance).data
            return success_response(data, status.HTTP_200_OK)
        except ValidationError:
            return error_response({"detail": "Tournament not found."}, status.HTTP_404_NOT_FOUND)
        except Exception:
            return error_response("Internal server error", status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, pk: int) -> Response:
        return self._update(request, pk, partial=False)

    def patch(self, request, pk: int) -> Response:
        return self._update(request, pk, partial=True)

    def _update(self, request, pk: int, partial: bool) -> Response:
        print("TournamentDetailView._update called with:", pk, request.data, "partial =", partial)
        try:
            instance = self.service.get(pk)
        except ValidationError:
            return error_response({"detail": "Tournament not found."}, status.HTTP_404_NOT_FOUND)

        serializer = UpdateTournamentSerializer(instance, data=request.data, partial=partial)
        try:
            serializer.is_valid(raise_exception=True)
            updated = self.service.update(pk, serializer.validated_data)  # type: ignore
            data = TournamentSerializer(updated).data
            return success_response(data, status.HTTP_200_OK)
        except ValidationError as e:
            payload = getattr(e, "message_dict", {"detail": str(e)})
            return error_response(payload, status.HTTP_400_BAD_REQUEST)
        except Exception:
            return error_response("Internal server error", status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk: int) -> Response:
        try:
            self.service.delete(pk)
            return success_response({"message": "Deleted successfully"}, status.HTTP_200_OK)
        except ValidationError:
            return error_response({"detail": "Tournament not found."}, status.HTTP_404_NOT_FOUND)
        except Exception:
            return error_response("Internal server error", status.HTTP_500_INTERNAL_SERVER_ERROR)
