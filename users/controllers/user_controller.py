from typing import Dict, Any
from rest_framework import status

from users.services.user_service import UserService
from users.exceptions import UserNotFoundException
from utils.response_handler import success_response, error_response


user_service = UserService()


def get_all_users_controller():
    try:
        users = user_service.list_users()
        return success_response(users)
    except Exception:
        return error_response('Internal server error', status.HTTP_500_INTERNAL_SERVER_ERROR)


def get_user_by_id_controller(user_id: int):
    try:
        user = user_service.retrieve_user(user_id)
        return success_response(user)
    except UserNotFoundException as e:
        return error_response(str(e), status.HTTP_404_NOT_FOUND)
    except Exception:
        return error_response('Internal server error', status.HTTP_500_INTERNAL_SERVER_ERROR)


def create_user_controller(data: Dict[str, Any]):
    try:
        user = user_service.create_user(data)
        return success_response(user, status.HTTP_201_CREATED)
    except Exception as e:
        # print("❌ Error al crear usuario:", repr(e))
        return error_response('Internal server error', status.HTTP_500_INTERNAL_SERVER_ERROR)


def update_user_controller(user_id: int, data: Dict[str, Any]):
    try:
        print('Actualizando usuario:', user_id)
        user = user_service.update_user(user_id, data)
        return success_response(user)
    except UserNotFoundException as e:
        return error_response(str(e), status.HTTP_404_NOT_FOUND)
    except Exception as e:
        # print("❌ Error al actualizar usuario:", repr(e))
        return error_response('Internal server error', status.HTTP_500_INTERNAL_SERVER_ERROR)


def delete_user_controller(user_id: int):
    try:
        user = user_service.delete_user(user_id)
        return success_response(user)
    except UserNotFoundException as e:
        return error_response(str(e), status.HTTP_404_NOT_FOUND)
    except Exception:
        return error_response('Internal server error', status.HTTP_500_INTERNAL_SERVER_ERROR)
