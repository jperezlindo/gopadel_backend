from typing import Any
from django.core.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from registrations.services.registration_service import RegistrationService
from registrations.schemas.registration_serializer import (
    RegistrationSerializer,
    CreateRegistrationSerializer,
    UpdateRegistrationSerializer,
)
from utils.response_handler import success_response, error_response


class RegistrationListCreateView(APIView):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.service = RegistrationService()

    def get(self, request) -> Response:
        try:
            filters = {
                k: v
                for k, v in {
                    "tournament_id": request.query_params.get("tournament_id"),
                    "tournament_category_id": request.query_params.get("tournament_category_id"),
                    "player_id": request.query_params.get("player_id"),
                    "status": request.query_params.get("status"),
                }.items()
                if v is not None
            }
            items = self.service.list(**filters)
            data = RegistrationSerializer(items, many=True).data
            return success_response(data, status.HTTP_200_OK)
        except Exception as e:
            return error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request) -> Response:
        try:
            serializer = CreateRegistrationSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance = self.service.create(serializer.validated_data)  # type: ignore
            data = RegistrationSerializer(instance).data
            return success_response(data, status.HTTP_201_CREATED)
        except ValidationError as ve:
            return error_response(str(ve), status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)


class RegistrationDetailView(APIView):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.service = RegistrationService()

    def get(self, request, pk: int) -> Response:
        try:
            instance = self.service.get(pk)
            if instance is None:
                return error_response("Registration not found.", status.HTTP_404_NOT_FOUND)
            data = RegistrationSerializer(instance).data
            return success_response(data, status.HTTP_200_OK)
        except Exception as e:
            return error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, pk: int) -> Response:
        try:
            serializer = UpdateRegistrationSerializer(data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            instance = self.service.update(pk, serializer.validated_data)  # type: ignore
            data = RegistrationSerializer(instance).data
            return success_response(data, status.HTTP_200_OK)
        except ValidationError as ve:
            return error_response(str(ve), status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk: int) -> Response:
        try:
            ok = self.service.delete(pk)
            if not ok:
                return error_response("Registration not found.", status.HTTP_404_NOT_FOUND)
            return success_response({"deleted": True}, status.HTTP_200_OK)
        except Exception as e:
            return error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)
