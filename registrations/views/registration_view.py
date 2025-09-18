# registrations/views/registration_view.py
"""
Como práctica de organización, re-exporto las vistas públicas desde este módulo
para que las urls importen desde 'registrations.views' y no acoplen al controller.
De esta forma mantengo la misma convención que en 'tournaments'.
"""

from registrations.controllers.registration_controller import (
    RegistrationListCreateView as RegistrationListCreateView,
    RegistrationDetailView as RegistrationDetailView,
)

# Expongo explícitamente lo que quiero que se importe desde afuera
__all__ = ["RegistrationListCreateView", "RegistrationDetailView"]
