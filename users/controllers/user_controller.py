from typing import Any
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError

from users.services.user_service import UserService
from users.schemas.user_serializer import (
    UserSerializer,
    CreateUserSerializer,
    UpdateUserSerializer,
)
from users.schemas.change_password_serializer import ChangePasswordSerializer
from utils.response_handler import success_response, error_response


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
            print('Error occurred while listing users:', e)
            return error_response("Internal server error", status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request) -> Response:
        try:
            serializer = CreateUserSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance = self.service.create(serializer.validated_data) # type: ignore
            data = UserSerializer(instance).data
            return success_response(data, status.HTTP_201_CREATED)
        except ValidationError as e:
            payload = getattr(e, "message_dict", {"detail": str(e)})
            return error_response(payload, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # print('Error occurred while creating user:', e)
            return error_response("Internal server error", status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserDetailView(APIView):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.service = UserService()

    def get(self, request, pk: int) -> Response:
        try:
            instance = self.service.get(pk)
            data = UserSerializer(instance).data
            return success_response(data, status.HTTP_200_OK)
        except ValidationError:
            return error_response({"detail": "User not found."}, status.HTTP_404_NOT_FOUND)
        except Exception:
            return error_response("Internal server error", status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, pk: int) -> Response:
        return self._update(request, pk, partial=False)

    def patch(self, request, pk: int) -> Response:
        return self._update(request, pk, partial=True)

    def delete(self, request, pk: int) -> Response:
        try:
            self.service.delete(pk)
            return success_response({"message": "Deleted successfully"}, status.HTTP_200_OK)
        except ValidationError:
            return error_response({"detail": "User not found."}, status.HTTP_404_NOT_FOUND)
        except Exception:
            return error_response("Internal server error", status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _update(self, request, pk: int, partial: bool) -> Response:
        try:
            instance = self.service.get(pk)
        except ValidationError:
            return error_response({"detail": "User not found."}, status.HTTP_404_NOT_FOUND)

        serializer = UpdateUserSerializer(instance, data=request.data, partial=partial)
        try:
            serializer.is_valid(raise_exception=True)
            updated = self.service.update(pk, serializer.validated_data) # type: ignore
            data = UserSerializer(updated).data
            return success_response(data, status.HTTP_200_OK)
        except ValidationError as e:
            payload = getattr(e, "message_dict", {"detail": str(e)})
            return error_response(payload, status.HTTP_400_BAD_REQUEST)
        except Exception:
            return error_response("Internal server error", status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserChangePasswordView(APIView):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.service = UserService()

    def post(self, request, pk: int) -> Response:
        # 1) Cargar target user (404 si no existe)
        try:
            target_user = self.service.get(pk)
        except ValidationError:
            return error_response({"detail": "User not found."}, status.HTTP_404_NOT_FOUND)

        # 2) Validar payload con contexto (actor y target)
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"actor": request.user, "target_user": target_user}
        )

        try:
            serializer.is_valid(raise_exception=True)
            old_password = serializer.validated_data.get("old_password") # type: ignore
            new_password = serializer.validated_data["new_password"] # type: ignore

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
        except ValidationError as e:
            payload = getattr(e, "message_dict", {"detail": str(e)})
            # Si vino del service con "User not found.", 404; sino 400
            code = status.HTTP_404_NOT_FOUND if payload.get("detail") == "User not found." else status.HTTP_400_BAD_REQUEST
            return error_response(payload, code)
        except Exception:
            return error_response("Internal server error", status.HTTP_500_INTERNAL_SERVER_ERROR)
