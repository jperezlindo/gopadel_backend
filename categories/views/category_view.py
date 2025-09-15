# categories/views/category_view.py
from categories.controllers.category_controller import (
    CategoryListView as CategoryListView,
    CategoryDetailView as CategoryDetailView,
)

__all__ = ["CategoryListView", "CategoryDetailView"]
