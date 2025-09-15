# categories/controllers/category_controller.py
from typing import Optional
from rest_framework.views import APIView
from rest_framework import status
from django.core.exceptions import ValidationError

from categories.services.category_service import CategoryService
from categories.schemas.category_serializers import CategorySerializer
from utils.response_handler import success_response, error_response  # existente en tu proyecto


def _parse_bool(value: Optional[str]) -> Optional[bool]:
    if value is None:
        return None
    v = value.strip().lower()
    if v in {"1", "true", "t", "yes", "y", "si", "sí"}:
        return True
    if v in {"0", "false", "f", "no", "n"}:
        return False
    return None  # inválido => ignoramos filtro


class CategoryListView(APIView):
    """
    GET /api/v1/categories/?is_active=true&search=pri
    """
    def get(self, request):
        is_active = _parse_bool(request.query_params.get("is_active"))
        search = request.query_params.get("search")

        service = CategoryService()
        qs = service.list_categories(is_active=is_active, search=search)
        data = CategorySerializer(qs, many=True).data
        return success_response(data, status.HTTP_200_OK)


class CategoryDetailView(APIView):
    """
    GET /api/v1/categories/<id>/
    """
    def get(self, request, pk: int):
        service = CategoryService()
        try:
            category = service.get_category(pk)
            data = CategorySerializer(category).data
            return success_response(data, status.HTTP_200_OK)
        except ValidationError as e:
            return error_response(str(e), status.HTTP_404_NOT_FOUND)
