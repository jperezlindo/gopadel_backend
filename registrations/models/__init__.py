# registrations/models/__init__.py
"""
Como práctica de arquitectura, centralizo los modelos públicos del módulo para
exponer una API clara hacia el resto del proyecto. Al re-exportar, simplifico
imports en services, repositories, serializers y tests.
"""

from .registration import Registration
from .registration_unavailability import RegistrationUnavailability

# Mantengo explícito qué expone el paquete para evitar fugas de símbolos internos
__all__ = [
    "Registration",
    "RegistrationUnavailability",
]
