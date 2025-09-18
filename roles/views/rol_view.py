# roles/views/rol_view.py
# Este archivo funciona como puente de importación estable desde urls.py.
# Se re-exportan los controllers para desacoplar el path real de la capa de vistas.

from roles.controllers.rol_controller import RolListView, RolDetailView

__all__ = ["RolListView", "RolDetailView"]
