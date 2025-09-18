# utils/exceptions.py
"""
Handler de excepciones centralizado para DRF.

Acá se unifica el formato de error para el front usando:
  - error_mapper.normalize_exception_payload / map_exception_status
  - response_handler.error_response

Estrategia:
- Se respeta lo que DRF mapea por defecto cuando corresponde, pero se normaliza
  el payload para que siempre llegue con claves coherentes (detail, non_field_errors, por-campo).
- Esto evita duplicar lógica en cada controller/service y asegura respuestas consistentes.
"""

from typing import Any, Dict
import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError

from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.exceptions import (
    ValidationError as DRFValidationError,
    NotFound,
    PermissionDenied,
    AuthenticationFailed,
    Throttled,
)
from rest_framework import status as http

from .error_mapper import (
    normalize_errors,
    normalize_exception_payload,
    map_exception_status,
)
from .response_handler import error_response

logger = logging.getLogger(__name__)


def _normalize_drf_response_data(data: Any) -> Dict[str, Any]:
    """
    Cuando DRF ya produjo un Response, su `data` puede venir en distintos formatos.
    Acá se normaliza a un contrato de errores consistente con el front.
    """
    return normalize_errors(data)


def custom_exception_handler(exc, context):
    """
    Handler registrado en settings.py (REST_FRAMEWORK.EXCEPTION_HANDLER).
    Objetivo: devolver SIEMPRE un error consistente para el front, con HTTP status correcto.
    """
    # 1) Prioridad al handler nativo de DRF para excepciones comunes.
    response = drf_exception_handler(exc, context)
    if response is not None:
        try:
            normalized = _normalize_drf_response_data(response.data)
        except Exception:  # pragma: no cover
            # Si algo raro pasa durante la normalización, se registra y se envía un detalle básico.
            logger.exception("Error normalizando respuesta DRF en custom_exception_handler")
            normalized = {"detail": ["Error procesando la respuesta de DRF."]}

        status_code = getattr(response, "status_code", http.HTTP_400_BAD_REQUEST)
        return error_response(normalized, status_code=status_code)

    # 2) Manejo explícito para excepciones no interceptadas por DRF o de dominio propio.
    # -- Validaciones de Django/DRF
    if isinstance(exc, (DjangoValidationError, DRFValidationError)):
        payload = normalize_exception_payload(exc)
        status_code = map_exception_status(exc)
        return error_response(payload, status_code=status_code)

    # -- Conflictos de integridad (unicidad, FK, etc.)
    if isinstance(exc, IntegrityError):
        payload = normalize_exception_payload(exc)
        status_code = map_exception_status(exc)
        return error_response(payload, status_code=status_code)

    # -- No encontrado (si llegara a escaparse del handler DRF)
    if isinstance(exc, NotFound):
        return error_response({"detail": ["No encontrado."]}, status_code=http.HTTP_404_NOT_FOUND)

    # -- Auth / permisos (ajusto semántica HTTP estándar)
    if isinstance(exc, AuthenticationFailed):
        # 401: no autenticado / credenciales inválidas
        return error_response({"detail": ["No autenticado."]}, status_code=http.HTTP_401_UNAUTHORIZED)

    if isinstance(exc, PermissionDenied):
        # 403: autenticado pero sin permisos
        return error_response({"detail": ["No autorizado."]}, status_code=http.HTTP_403_FORBIDDEN)

    # -- Rate limiting / throttling
    if isinstance(exc, Throttled):
        detail = getattr(exc, "detail", {"detail": ["Demasiadas solicitudes."]})
        payload = normalize_errors(detail)
        return error_response(payload, status_code=http.HTTP_429_TOO_MANY_REQUESTS)

    # 3) Fallback: error inesperado. Se registra y devuelve 500 genérico.
    logger.exception("Unhandled exception en custom_exception_handler", exc_info=exc)
    return error_response({"detail": ["Error interno del servidor."]}, status_code=http.HTTP_500_INTERNAL_SERVER_ERROR)
