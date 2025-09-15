# categories/services/category_service.py
from typing import Optional
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from categories.models.category import Category
from categories.repositories.category_repository import CategoryRepository

class CategoryService:
    def __init__(self, repo: Optional[CategoryRepository] = None) -> None:
        self.repo = repo or CategoryRepository()

    def list_categories(self, *, is_active: Optional[bool] = None, search: Optional[str] = None) -> QuerySet[Category]:
        return self.repo.list(is_active=is_active, search=search)

    def get_category(self, pk: int) -> Category:
        item = self.repo.get_by_id(pk)
        if not item:
            # Por convención del proyecto usamos ValidationError para "not found"
            raise ValidationError("Category not found")
        return item
