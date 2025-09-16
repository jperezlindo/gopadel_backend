# registrations/controllers/registration_controller.py
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError

from registrations.services.registration_service import RegistrationService
from registrations.schemas.registration_serializers import (
    RegistrationReadSerializer,
    RegistrationWriteSerializer,
)
from utils.response_handler import success_response, error_response


class RegistrationListCreateView(APIView):
    service = RegistrationService()

    def get(self, request: Request) -> Response:
        tc_id = request.query_params.get("tournament_category_id")
        items = (
            self.service.list(int(tc_id)) if (tc_id and str(tc_id).isdigit()) else self.service.list()
        )
        data = RegistrationReadSerializer(items, many=True).data
        return success_response(data=data)

    def post(self, request: Request) -> Response:
        serializer = RegistrationWriteSerializer(data=request.data)
        if not serializer.is_valid():
            # error_response acepta dict/list/str y normaliza; pasamos el dict de errors
            return error_response(message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        try:
            reg = self.service.create(**serializer.validated_data)  # type: ignore[arg-type]
            data = RegistrationReadSerializer(reg).data
            return success_response(data=data, status_code=status.HTTP_201_CREATED)
        except ValidationError as e:
            # e puede traer message_dict o string; nuestro helper lo normaliza
            payload = getattr(e, "message_dict", str(e))
            return error_response(message=payload, status_code=status.HTTP_400_BAD_REQUEST)


class RegistrationDetailView(APIView):
    service = RegistrationService()

    def get(self, request: Request, pk: int) -> Response:
        try:
            reg = self.service.get(pk)
            data = RegistrationReadSerializer(reg).data
            return success_response(data=data)
        except ValidationError as e:
            payload = getattr(e, "message_dict", str(e))
            return error_response(message=payload, status_code=status.HTTP_404_NOT_FOUND)

    def delete(self, request: Request, pk: int) -> Response:
        try:
            self.service.delete(pk)
            return success_response(data={"message": "Registro eliminado."})
        except ValidationError as e:
            payload = getattr(e, "message_dict", str(e))
            return error_response(message=payload, status_code=status.HTTP_404_NOT_FOUND)
