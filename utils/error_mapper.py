# utils/error_mapper.py
from typing import Iterable, Set
from django.core.exceptions import ValidationError
from rest_framework import status

def _collect_codes(exc: ValidationError) -> Set[str]:
    codes: Set[str] = set()

    # Estructura tipo dict: {'field': ['msg'], ...} con códigos
    if hasattr(exc, 'error_dict') and exc.error_dict:
        for field_errors in exc.error_dict.values():
            for err in field_errors:
                if getattr(err, 'code', None):
                    codes.add(err.code) # type: ignore
        return codes

    # Lista plana de errores
    if hasattr(exc, 'error_list') and exc.error_list:
        for err in exc.error_list:
            if getattr(err, 'code', None):
                codes.add(err.code) # type: ignore
        return codes

    # Un solo mensaje
    if getattr(exc, 'code', None):
        codes.add(exc.code) # type: ignore

    return codes

def map_validation_error_status(exc: ValidationError) -> int:
    """
    Convierte códigos de ValidationError a HTTP status.
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
