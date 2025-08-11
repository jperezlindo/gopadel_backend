from typing import cast, Dict, Any, Tuple, Optional
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status

from users.schemas.user_serializer import CreateUserSerializer
from users.schemas.update_user_serializer import UpdateUserSerializer
from users.controllers import user_controller


def validate_serializer(serializer_class, data, partial: bool = False) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Helper function to validate a serializer and return validated data or errors.
    """
    serializer = serializer_class(data=data, partial=partial)
    if serializer.is_valid():
        validated_data = cast(Dict[str, Any], serializer.validated_data)
        return validated_data, None
    return None, serializer.errors


class UserListCreateView(APIView):
    """
    Handles listing all users and creating a new user.
    """

    def get(self, request: Request) -> Response:
        """
        List all active users.
        """
        return user_controller.get_all_users_controller()

    def post(self, request: Request) -> Response:
        """
        Create a new user with validated data.
        """
        validated_data, errors = validate_serializer(CreateUserSerializer, request.data)
        if errors:
            return Response(errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        return user_controller.create_user_controller(validated_data)  # type: ignore


class UserRetrieveUpdateDestroyView(APIView):
    """
    Handles retrieving, updating, partially updating, and deleting a user by ID.
    """

    def get(self, request: Request, user_id: int) -> Response:
        """
        Retrieve a single user by ID.
        """
        return user_controller.get_user_by_id_controller(user_id)

    def put(self, request: Request, user_id: int) -> Response:
        """
        Fully update a user by ID.
        """
        validated_data, errors = validate_serializer(UpdateUserSerializer, request.data)
        if errors:
            return Response(errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        return user_controller.update_user_controller(user_id, validated_data) # type: ignore


    def patch(self, request: Request, user_id: int) -> Response:
        """
        Partially update a user by ID.
        """
        validated_data, errors = validate_serializer(UpdateUserSerializer, request.data, partial=True)
        if errors:
            return Response(errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        return user_controller.update_user_controller(user_id, validated_data) # type: ignore


    def delete(self, request: Request, user_id: int) -> Response:
        """
        Delete a user by ID (soft delete recommended).
        """
        return user_controller.delete_user_controller(user_id)
