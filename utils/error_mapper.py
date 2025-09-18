# utils/error_mapper.py
from typing import Any, Dict, List, Tuple, Union, Set
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework import status

# En este módulo centralizo la normalización de payloads de error y el mapeo a HTTP status.
# Objetivo: que el front reciba siempre un formato estable sin importar la fuente del error.

Payload = Union[Dict[str, Any], List[Any], Tuple[Any, ...], str, None]


# ---------------- Normalización de payloads ----------------
def _as_list(val: Any) -> List[str]:
    # Aseguro que cualquier valor se convierta en lista de strings para mantener consistencia.
    if val is None:
        return []
    if isinstance(val, (list, tuple)):
        return [str(v) for v in val]
    return [str(val)]


def normalize_errors(err: Payload) -> Dict[str, List[str]]:
    """
    Convierte distintos formatos de error en un dict[str, list[str]] estable:
      - dict -> {campo: [msgs]}
      - list/tuple -> {"non_field_errors": [...]}
      - str/None/otros -> {"detail": ["..."]}
    """
    if isinstance(err, dict):
        out: Dict[str, List[str]] = {}
        for k, v in err.items():
            out[str(k)] = _as_list(v)
        return out
    if isinstance(err, (list, tuple)):
        return {"non_field_errors": _as_list(err)}
    if err is None:
        return {"detail": ["Unknown error"]}
    return {"detail": [str(err)]}


# ---------------- Mapeo de códigos a HTTP status (Django ValidationError) ----------------
# Acá detecto códigos de error para traducirlos a un status HTTP coherente para el cliente.

def _collect_codes(exc: DjangoValidationError) -> Set[str]:
    # Extraigo códigos de error desde las estructuras posibles de DjangoValidationError.
    codes: Set[str] = set()

    # Estructura tipo dict: {'field': [ErrorList], ...}
    if hasattr(exc, 'error_dict') and exc.error_dict:
        for field_errors in exc.error_dict.values():
            for err in field_errors:
                code = getattr(err, 'code', None)
                if code:
                    codes.add(str(code))
        return codes

    # Lista plana de errores
    if hasattr(exc, 'error_list') and exc.error_list:
        for err in exc.error_list:
            code = getattr(err, 'code', None)
            if code:
                codes.add(str(code))
        return codes

    # Un solo mensaje
    code = getattr(exc, 'code', None)
    if code:
        codes.add(str(code))

    return codes


def map_validation_error_status(exc: DjangoValidationError) -> int:
    """
    Convierte códigos de ValidationError (Django) a HTTP status.
    - not_found  -> 404
    - conflict / unique / duplicate -> 409
    - default -> 400
    """
    codes = _collect_codes(exc)

    if 'not_found' in codes:
        return status.HTTP_404_NOT_FOUND

    if {'conflict', 'unique', 'duplicate'} & codes:
        return status.HTTP_409_CONFLICT

    return status.HTTP_400_BAD_REQUEST


# ---------------- Mapeo general de Exception -> HTTP status ----------------
def map_exception_status(exc: Exception) -> int:
    """
    Determina un HTTP status sensato según el tipo de excepción.
    - DjangoValidationError: usa map_validation_error_status
    - DRFValidationError: 400
    - IntegrityError: 409 si huele a unicidad, si no 400
    - default: 400
    """
    if isinstance(exc, DjangoValidationError):
        return map_validation_error_status(exc)

    if isinstance(exc, DRFValidationError):
        return status.HTTP_400_BAD_REQUEST

    if isinstance(exc, IntegrityError):
        msg = str(exc).lower()
        if any(k in msg for k in ('unique', 'duplicate', 'already exists')):
            return status.HTTP_409_CONFLICT
        return status.HTTP_400_BAD_REQUEST

    return status.HTTP_400_BAD_REQUEST


# ---------------- Helpers de normalización específicos (opcionales) ----------------
def normalize_exception_payload(exc: Exception) -> Dict[str, List[str]]:
    """
    Intenta extraer un payload por-campo cuando es posible.
    - DjangoValidationError: usa message_dict/messages
    - DRFValidationError: usa .detail
    - IntegrityError: trata de inferir 'unique' -> non_field_errors
    - default: detail genérico
    """
    if isinstance(exc, DjangoValidationError):
        raw = getattr(exc, "message_dict", getattr(exc, "messages", str(exc)))
        return normalize_errors(raw)

    if isinstance(exc, DRFValidationError):
        raw = getattr(exc, "detail", str(exc))
        return normalize_errors(raw)

    if isinstance(exc, IntegrityError):
        # Si se necesitara, acá se podría mapear un campo específico según el backend.
        return {"non_field_errors": ["Violación de integridad de datos."]}

    return {"detail": [str(exc) or "Unknown error"]}
