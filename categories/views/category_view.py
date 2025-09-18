# categories/views/category_view.py
"""
Puente de vistas para la app de Categories.

Decisión:
- Centralizo aquí los re-exports de las vistas (controllers) para mantener una
  ruta de import limpia y estable desde urls. De esta forma:
    from categories.views.category_view import CategoryListView, CategoryDetailView
  y evito que urls dependa directamente de la estructura interna de controllers.
- Si mañana reorganizo controllers o subdivido vistas, solo toco este archivo
  y el resto del proyecto (urls) sigue intacto.
"""

# Importo las vistas reales desde controllers y las renombro explícitamente.
from categories.controllers.category_controller import (
    CategoryListView as CategoryListView,
    CategoryDetailView as CategoryDetailView,
)

# Expongo únicamente lo que necesito que sea público para otras capas (urls).
__all__ = ["CategoryListView", "CategoryDetailView"]
