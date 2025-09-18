# registrations/controllers/registration_controller.py
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from registrations.services.registration_service import RegistrationService
from registrations.schemas.registration_serializers import (
    RegistrationReadSerializer,
    RegistrationWriteSerializer,
)
from utils.response_handler import success_response, error_response


class RegistrationListCreateView(APIView):
    """
    Defino el endpoint de listado/creación de inscripciones.
    - GET permite filtrar por ?tournament_category_id=<id>.
    - POST crea la inscripción y opcionalmente persiste las indisponibilidades horarias.
    Mantengo la orquestación fina acá y dejo la lógica de negocio en el service.
    """
    service = RegistrationService()

    def get(self, request: Request) -> Response:
        # Prefiero tolerar tc_id vacío o inválido sin romper; si no es dígito, ignoro el filtro.
        tc_id = request.query_params.get("tournament_category_id")
        items = (
            self.service.list(int(tc_id)) if (tc_id and str(tc_id).isdigit()) else self.service.list()
        )
        data = RegistrationReadSerializer(items, many=True).data
        return success_response(data=data)

    def post(self, request: Request) -> Response:
        # Valido payload con el serializer de escritura para asegurar tipos/forma antes del service.
        serializer = RegistrationWriteSerializer(data=request.data)
        if not serializer.is_valid():
            # error_response acepta dict/list/str y normaliza.
            return error_response(message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        try:
            # Paso validated_data al service, que maneja reglas de negocio y transacción.
            reg = self.service.create(**serializer.validated_data)  # type: ignore[arg-type]
            data = RegistrationReadSerializer(reg).data
            return success_response(data=data, status_code=status.HTTP_201_CREATED)
        except ValidationError as e:
            payload = getattr(e, "message_dict", str(e))
            return error_response(message=payload, status_code=status.HTTP_400_BAD_REQUEST)
        except IntegrityError:
            # Si brigara un UniqueConstraint (pareja duplicada, etc.), respondo 400 claro para el front.
            return error_response(
                message="Conflicto de unicidad al crear la inscripción.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )


class RegistrationDetailView(APIView):
    """
    Expongo GET/DELETE/PATCH para una inscripción puntual.
    - GET devuelve la inscripción con sus indisponibilidades.
    - DELETE elimina la inscripción.
    - PATCH permite actualizar campos simples y, si viene 'unavailability', reemplaza por completo
      (la lógica de reemplazo vive en el serializer.update según lo definido).
    """
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
            # Mantengo 200 con mensaje estandarizado para feedback explícito en el front.
            return success_response(data={"message": "Registro eliminado."})
        except ValidationError as e:
            payload = getattr(e, "message_dict", str(e))
            return error_response(message=payload, status_code=status.HTTP_404_NOT_FOUND)

    def patch(self, request: Request, pk: int) -> Response:
        """
        Para actualizaciones parciales uso el serializer con partial=True.
        - Si el payload incluye 'unavailability', el serializer reemplaza completamente los bloques
          (delete + bulk_create), respetando la convención acordada.
        - Si el payload no incluye 'unavailability', no toco los bloques existentes.
        """
        try:
            reg = self.service.get(pk)
        except ValidationError as e:
            payload = getattr(e, "message_dict", str(e))
            return error_response(message=payload, status_code=status.HTTP_404_NOT_FOUND)

        serializer = RegistrationWriteSerializer(instance=reg, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        try:
            # Uso serializer.save() porque ya implementa la estrategia de reemplazo total de unavailability.
            updated = serializer.save()
            data = RegistrationReadSerializer(updated).data
            return success_response(data=data)
        except ValidationError as e:
            payload = getattr(e, "message_dict", str(e))
            return error_response(message=payload, status_code=status.HTTP_400_BAD_REQUEST)
        except IntegrityError:
            # Si fallara por constraints (p. ej., pareja duplicada tras el cambio), devuelvo 400 claro.
            return error_response(
                message="Conflicto de unicidad al actualizar la inscripción.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
