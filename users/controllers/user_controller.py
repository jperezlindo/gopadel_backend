# users/controllers/user_controller.py
from typing import Any
from django.db import IntegrityError
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError

from users.services.user_service import UserService
from users.schemas.user_serializer import (
    UserSerializer,
    CreateUserSerializer,
    UpdateUserSerializer,
)
from users.schemas.change_password_serializer import ChangePasswordSerializer
from utils.response_handler import success_response, error_response
from utils.pagination import DefaultPagination  # <-- uso el paginador unificado


# ---------------- Helpers de normalización ----------------
def _as_list(val):
    # Normalizo cualquier cosa a lista de strings para mantener consistencia.
    if val is None:
        return []
    if isinstance(val, (list, tuple)):
        return [str(v) for v in val]
    return [str(val)]


def normalize_errors(err):
    """
    Devuelvo dict[str, list[str]] estable para la UI.
    - dict -> {campo: [msgs]}
    - list/tuple -> {"non_field_errors": [...]}
    - str  -> {"detail": ["..."]}
    """
    if isinstance(err, dict):
        out = {}
        for k, v in err.items():
            out[str(k)] = _as_list(v)
        return out
    if isinstance(err, (list, tuple)):
        return {"non_field_errors": _as_list(err)}
    return {"detail": [str(err)]}


class UserListCreateView(APIView):
    """
    Expongo listado y creación de usuarios.

    Decisiones:
    - En GET pagino usando DefaultPagination para devolver metadatos
      esperados por el front (count, page, page_size, total_pages, results).
    - En POST valido con CreateUserSerializer y delego la creación al service.
    """

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.service = UserService()
        # Instancio el paginador para este controller
        self.paginator = DefaultPagination()

    def get(self, request) -> Response:
        """
        Listado paginado de usuarios.
        Nota: por ahora no aplico filtros por query params; si hace falta más adelante,
        se pasa el filtrado al service/repository y acá solo se recogen los params.
        """
        try:
            queryset = self.service.list()
            page = self.paginator.paginate_queryset(queryset, request, view=self)

            # Serializo solo la página actual
            serialized = UserSerializer(page, many=True).data

            # Armo la respuesta paginada con el contrato del paginador unificado
            paginated = self.paginator.get_paginated_response(serialized)
            # Devuelvo el payload paginado tal cual (success_response no re-envuelve)
            return success_response(paginated.data, status.HTTP_200_OK)

        except Exception:
            # logger.exception("Error listing users")
            return error_response({"detail": ["Internal server error"]}, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request) -> Response:
        """
        Creación de usuario.
        - Valido payload con CreateUserSerializer.
        - Si hay errores de validación, normalizo para la UI.
        - Si todo está OK, creo el usuario vía service y devuelvo 201.
        """
        try:
            serializer = CreateUserSerializer(data=request.data)

            if not serializer.is_valid():
                return error_response(normalize_errors(serializer.errors), status.HTTP_400_BAD_REQUEST)

            instance = self.service.create(serializer.validated_data)  # type: ignore
            data = UserSerializer(instance).data
            return success_response(data, status.HTTP_201_CREATED)

        except DRFValidationError as e:
            payload = normalize_errors(getattr(e, "detail", str(e)))
            return error_response(payload, status.HTTP_400_BAD_REQUEST)

        except DjangoValidationError as e:
            payload = getattr(e, "message_dict", getattr(e, "messages", str(e)))
            return error_response(normalize_errors(payload), status.HTTP_400_BAD_REQUEST)

        except IntegrityError as e:
            # Manejo unicidad de email a nivel DB por si se escapa del serializer.
            msg = str(e).lower()
            if "email" in msg and "unique" in msg:
                return error_response({"email": ["Este email ya está registrado."]}, status.HTTP_400_BAD_REQUEST)
            return error_response({"non_field_errors": ["Violación de integridad de datos."]}, status.HTTP_400_BAD_REQUEST)

        except Exception:
            # logger.exception("Error creating user")
            return error_response({"detail": ["Internal server error"]}, status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserDetailView(APIView):
    """
    Expongo detalle, actualización y borrado lógico (soft-delete) de usuarios.

    Decisiones:
    - get(): 404 si no existe (service levanta not_found y el handler lo mapea).
    - put/patch(): actualizo con UpdateUserSerializer (no toco password acá).
    - delete(): soft-delete (is_deleted=True, is_active=False) vía service.
    """

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.service = UserService()

    def get(self, request, pk: int) -> Response:
        try:
            instance = self.service.get(pk)
            data = UserSerializer(instance).data
            return success_response(data, status.HTTP_200_OK)
        except DjangoValidationError:
            return error_response({"detail": ["User not found."]}, status.HTTP_404_NOT_FOUND)
        except Exception:
            return error_response({"detail": ["Internal server error"]}, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, pk: int) -> Response:
        # PUT total: partial=False
        return self._update(request, pk, partial=False)

    def patch(self, request, pk: int) -> Response:
        # PATCH parcial: partial=True
        return self._update(request, pk, partial=True)

    def delete(self, request, pk: int) -> Response:
        try:
            self.service.delete(pk)
            return success_response({"message": "Deleted successfully"}, status.HTTP_200_OK)
        except DjangoValidationError:
            return error_response({"detail": ["User not found."]}, status.HTTP_404_NOT_FOUND)
        except Exception:
            return error_response({"detail": ["Internal server error"]}, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _update(self, request, pk: int, partial: bool) -> Response:
        """
        Flujo común para PUT/PATCH:
        - Valido payload con UpdateUserSerializer.
        - Delego actualización al service.
        - Normalizo errores en caso de validación o integridad.
        """
        try:
            instance = self.service.get(pk)
        except DjangoValidationError:
            return error_response({"detail": ["User not found."]}, status.HTTP_404_NOT_FOUND)

        serializer = UpdateUserSerializer(instance, data=request.data, partial=partial)
        try:
            if not serializer.is_valid():
                return error_response(normalize_errors(serializer.errors), status.HTTP_400_BAD_REQUEST)

            updated = self.service.update(pk, serializer.validated_data)  # type: ignore
            data = UserSerializer(updated).data
            return success_response(data, status.HTTP_200_OK)

        except DRFValidationError as e:
            payload = normalize_errors(getattr(e, "detail", str(e)))
            return error_response(payload, status.HTTP_400_BAD_REQUEST)

        except DjangoValidationError as e:
            payload = getattr(e, "message_dict", getattr(e, "messages", str(e)))
            return error_response(normalize_errors(payload), status.HTTP_400_BAD_REQUEST)

        except IntegrityError as e:
            msg = str(e).lower()
            if "email" in msg and "unique" in msg:
                return error_response({"email": ["Este email ya está registrado."]}, status.HTTP_400_BAD_REQUEST)
            return error_response({"non_field_errors": ["Violación de integridad de datos."]}, status.HTTP_400_BAD_REQUEST)

        except Exception:
            return error_response({"detail": ["Internal server error"]}, status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserChangePasswordView(APIView):
    """
    Expongo cambio de password:
    - Admins pueden cambiar la contraseña de cualquiera sin old_password.
    - Usuarios finales solo pueden cambiar su propia contraseña y deben enviar old_password.
    """

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.service = UserService()

    def post(self, request, pk: int) -> Response:
        # 1) Cargo target user (404 si no existe)
        try:
            target_user = self.service.get(pk)
        except DjangoValidationError:
            return error_response({"detail": ["User not found."]}, status.HTTP_404_NOT_FOUND)

        # 2) Valido payload con contexto (actor y target)
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"actor": request.user, "target_user": target_user}
        )

        try:
            if not serializer.is_valid():
                return error_response(normalize_errors(serializer.errors), status.HTTP_400_BAD_REQUEST)

            old_password = serializer.validated_data.get("old_password")  # type: ignore
            new_password = serializer.validated_data["new_password"]       # type: ignore

            # 3) Cambiar password vía service
            updated = self.service.change_password(
                actor=request.user,
                target_user_id=pk,
                old_password=old_password,
                new_password=new_password,
            )
            return success_response(
                {"message": "Password updated successfully.", "user": UserSerializer(updated).data},
                status.HTTP_200_OK
            )

        except DRFValidationError as e:
            payload = normalize_errors(getattr(e, "detail", str(e)))
            # Si vino "User not found." lo convierto en 404
            code = status.HTTP_404_NOT_FOUND if payload.get("detail") == ["User not found."] else status.HTTP_400_BAD_REQUEST
            return error_response(payload, code)

        except DjangoValidationError as e:
            payload = getattr(e, "message_dict", getattr(e, "messages", str(e)))
            return error_response(normalize_errors(payload), status.HTTP_400_BAD_REQUEST)

        except Exception:
            return error_response({"detail": ["Internal server error"]}, status.HTTP_500_INTERNAL_SERVER_ERROR)
