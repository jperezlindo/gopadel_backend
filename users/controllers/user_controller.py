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


# ---------------- Helpers de normalización ----------------

def _as_list(val):
    if val is None:
        return []
    if isinstance(val, (list, tuple)):
        return [str(v) for v in val]
    return [str(val)]

def normalize_errors(err):
    """
    Devuelve dict[str, list[str]] estable para la UI.
    - dict -> {campo: [msgs]}
    - list/tuple -> {"non_field_errors": [...]}
    - str -> {"detail": "..."}
    """
    if isinstance(err, dict):
        out = {}
        for k, v in err.items():
            out[str(k)] = _as_list(v)
        return out
    if isinstance(err, (list, tuple)):
        return {"non_field_errors": _as_list(err)}
    return {"detail": str(err)}


class UserListCreateView(APIView):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.service = UserService()

    def get(self, request) -> Response:
        try:
            items = self.service.list()
            data = UserSerializer(items, many=True).data
            return success_response(data, status.HTTP_200_OK)
        except Exception as e:
            # logger.exception("Error listing users")
            return error_response({"detail": "Internal server error"}, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request) -> Response:
        try:
            serializer = CreateUserSerializer(data=request.data)

            # No levantamos excepción automática: devolvemos errores normalizados
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
            # Por si la unicidad de email se valida a nivel DB
            msg = str(e).lower()
            if "email" in msg and "unique" in msg:
                return error_response({"email": ["Este email ya está registrado."]}, status.HTTP_400_BAD_REQUEST)
            return error_response({"non_field_errors": ["Violación de integridad de datos."]}, status.HTTP_400_BAD_REQUEST)

        except Exception:
            # logger.exception("Error creating user")
            return error_response({"detail": "Internal server error"}, status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserDetailView(APIView):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.service = UserService()

    def get(self, request, pk: int) -> Response:
        try:
            instance = self.service.get(pk)
            data = UserSerializer(instance).data
            return success_response(data, status.HTTP_200_OK)
        except DjangoValidationError:
            return error_response({"detail": "User not found."}, status.HTTP_404_NOT_FOUND)
        except Exception:
            return error_response({"detail": "Internal server error"}, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, pk: int) -> Response:
        return self._update(request, pk, partial=False)

    def patch(self, request, pk: int) -> Response:
        return self._update(request, pk, partial=True)

    def delete(self, request, pk: int) -> Response:
        try:
            self.service.delete(pk)
            return success_response({"message": "Deleted successfully"}, status.HTTP_200_OK)
        except DjangoValidationError:
            return error_response({"detail": "User not found."}, status.HTTP_404_NOT_FOUND)
        except Exception:
            return error_response({"detail": "Internal server error"}, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _update(self, request, pk: int, partial: bool) -> Response:
        try:
            instance = self.service.get(pk)
        except DjangoValidationError:
            return error_response({"detail": "User not found."}, status.HTTP_404_NOT_FOUND)

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
            return error_response({"detail": "Internal server error"}, status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserChangePasswordView(APIView):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.service = UserService()

    def post(self, request, pk: int) -> Response:
        # 1) Cargar target user (404 si no existe)
        try:
            target_user = self.service.get(pk)
        except DjangoValidationError:
            return error_response({"detail": "User not found."}, status.HTTP_404_NOT_FOUND)

        # 2) Validar payload con contexto (actor y target)
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"actor": request.user, "target_user": target_user}
        )

        try:
            if not serializer.is_valid():
                return error_response(normalize_errors(serializer.errors), status.HTTP_400_BAD_REQUEST)

            old_password = serializer.validated_data.get("old_password")  # type: ignore
            new_password = serializer.validated_data["new_password"]  # type: ignore

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
            # si vino "User not found." lo convertimos en 404
            code = status.HTTP_404_NOT_FOUND if payload.get("detail") == ["User not found."] else status.HTTP_400_BAD_REQUEST
            return error_response(payload, code)

        except DjangoValidationError as e:
            payload = getattr(e, "message_dict", getattr(e, "messages", str(e)))
            return error_response(normalize_errors(payload), status.HTTP_400_BAD_REQUEST)

        except Exception:
            return error_response({"detail": "Internal server error"}, status.HTTP_500_INTERNAL_SERVER_ERROR)