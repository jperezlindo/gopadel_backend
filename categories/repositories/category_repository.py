# categories/repositories/category_repository.py
from typing import Optional, Iterable
from django.db.models import QuerySet
from categories.models.category import Category

class CategoryRepository:
    def list(self, *, is_active: Optional[bool] = None, search: Optional[str] = None) -> QuerySet[Category]:
        qs = Category.objects.all().order_by("id")
        if is_active is not None:
            qs = qs.filter(is_active=is_active)
        if search:
            qs = qs.filter(name__icontains=search.strip())
        return qs

    def get_by_id(self, pk: int) -> Optional[Category]:
        try:
            return Category.objects.get(pk=pk)
        except Category.DoesNotExist:
            return None
