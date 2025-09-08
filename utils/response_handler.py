# utils/response_handler.py
from typing import Any, Dict, List, Tuple, Union
from rest_framework.response import Response
from rest_framework import status

Payload = Union[Dict[str, Any], List[Any], Tuple[Any, ...], str, None]

def success_response(data: Any, status_code: int = status.HTTP_200_OK) -> Response:
    """
    Devuelve data tal cual, con el status indicado.
    """
    return Response(data, status=status_code)

def error_response(message: Payload, status_code: int = status.HTTP_400_BAD_REQUEST) -> Response:
    """
    Normaliza el payload de error para el front:
      - dict -> se retorna tal cual (p.ej. {"email": ["Ya existe."]})
      - list/tuple -> {"non_field_errors": ["..."]}
      - str/otros -> {"detail": "..."}
    """
    if isinstance(message, dict):
        data = message  # ya está en formato por-campo o {"detail": "..."}
    elif isinstance(message, (list, tuple)):
        data = {"non_field_errors": [str(v) for v in message]}
    elif message is None:
        data = {"detail": "Unknown error"}
    else:
        data = {"detail": str(message)}

    return Response(data, status=status_code)
