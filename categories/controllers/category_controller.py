# categories/controllers/category_controller.py
# En este controller me enfoco en:
# - Parsear inputs (query/body)
# - Delegar el negocio al service
# - Serializar y devolver respuestas con nuestros helpers
# Importante: NO importo ningún urls.py para evitar ciclos en el URLConf.

from typing import Optional, Any

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny  # Por ahora dejo acceso abierto (ajusto más adelante si hace falta)
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError

from categories.services.category_service import CategoryService
from categories.schemas.category_serializers import (
    CategoryReadSerializer,
    # Si tenés serializers específicos para write, descomentá y usalos:
    # CategoryCreateSerializer,
    # CategoryUpdateSerializer,
)
from utils.pagination import DefaultPagination
from utils.response_handler import success_response, error_response


# ---------------- Helpers de parseo/normalización ----------------
def _parse_bool(value: Optional[str]) -> Optional[bool]:
    """
    Convierto valores de query string a booleanos reales:
    - true/1/yes/sí -> True
    - false/0/no    -> False
    - None/otro     -> None (sin filtro)
    """
    if value is None:
        return None
    v = value.strip().lower()
    if v in {"1", "true", "t", "yes", "y", "si", "sí"}:
        return True
    if v in {"0", "false", "f", "no", "n"}:
        return False
    return None  # inválido => no aplico filtro


def _as_list(val: Any):
    if val is None:
        return []
    if isinstance(val, (list, tuple)):
        return [str(v) for v in val]
    return [str(val)]


def _normalize_errors(err: Any):
    """
    Devuelvo dict[str, list[str]] estable para la UI:
    - dict -> {campo: [msgs]}
    - list/tuple -> {"non_field_errors": [...]}
    - str  -> {"detail": ["..."]}
    """
    if isinstance(err, dict):
        out = {}
        for k, v in err.items():
            out[str(k)] = _as_list(v)
        return out
    if isinstance(err, (list, tuple)):
        return {"non_field_errors": _as_list(err)}
    return {"detail": [str(err)]}


# =========================
# Listado + creación
# =========================
class CategoryListCreateView(APIView):
    """
    GET  /api/v1/categories/?is_active=true&search=pre&order_by=name
    POST /api/v1/categories/

    Decisiones:
    - En GET uso DefaultPagination para el contrato {count, page, page_size, total_pages, next, previous, results}.
    - En POST delego la creación al service y devuelvo el recurso con el serializer de lectura.
      (Si más adelante quiero validación de entrada más estricta, conecto CategoryCreateSerializer).
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        try:
            # 1) Parseo filtros desde query string
            is_active = _parse_bool(request.query_params.get("is_active"))
            search = request.query_params.get("search")
            order_by = request.query_params.get("order_by")

            # 2) Llamo al service para obtener el queryset filtrado
            service = CategoryService()
            qs = service.list_categories(is_active=is_active, search=search, order_by=order_by)

            # 3) Paginación unificada
            paginator = DefaultPagination()
            page = paginator.paginate_queryset(qs, request)

            # 4) Serializo la página resultante
            data = CategoryReadSerializer(page, many=True).data

            # 5) Devuelvo la respuesta paginada tal cual la arma nuestro paginador
            return paginator.get_paginated_response(data)

        except Exception:
            # logger.exception("Error listing categories")
            return error_response({"detail": ["Internal server error"]}, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            # Si tenés serializer de entrada, validá acá:
            # serializer = CategoryCreateSerializer(data=request.data)
            # if not serializer.is_valid():
            #     return error_response(_normalize_errors(serializer.errors), status.HTTP_400_BAD_REQUEST)
            # payload = serializer.validated_data

            payload = request.data  # Uso los datos crudos si aún no hay serializer de write
            service = CategoryService()
            instance = service.create_category(payload)  # Debe devolver la instancia creada

            data = CategoryReadSerializer(instance).data
            return success_response(data, status.HTTP_201_CREATED)

        except DRFValidationError as e:
            return error_response(_normalize_errors(getattr(e, "detail", str(e))), status.HTTP_400_BAD_REQUEST)
        except DjangoValidationError as e:
            payload = getattr(e, "message_dict", getattr(e, "messages", str(e)))
            return error_response(_normalize_errors(payload), status.HTTP_400_BAD_REQUEST)
        except IntegrityError:
            return error_response({"non_field_errors": ["Integrity error."]}, status.HTTP_400_BAD_REQUEST)
        except Exception:
            # logger.exception("Error creating category")
            return error_response({"detail": ["Internal server error"]}, status.HTTP_500_INTERNAL_SERVER_ERROR)


# =========================
# Detalle / actualización / borrado
# =========================
class CategoryDetailView(APIView):
    """
    GET    /api/v1/categories/<id>/
    PUT    /api/v1/categories/<id>/
    PATCH  /api/v1/categories/<id>/
    DELETE /api/v1/categories/<id>/

    Decisiones:
    - Dejo que el service levante ValidationError(code='not_found') si no existe y confío en nuestro handler.
    - En updates, si más adelante tengo serializer de write, lo conecto como en users/tournaments.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, pk: int):
        try:
            service = CategoryService()
            instance = service.get_category(pk)
            data = CategoryReadSerializer(instance).data
            return success_response(data, status.HTTP_200_OK)
        except DjangoValidationError:
            return error_response({"detail": ["Category not found."]}, status.HTTP_404_NOT_FOUND)
        except Exception:
            return error_response({"detail": ["Internal server error"]}, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, pk: int):
        return self._update(request, pk, partial=False)

    def patch(self, request, pk: int):
        return self._update(request, pk, partial=True)

    def delete(self, request, pk: int):
        try:
            service = CategoryService()
            service.delete_category(pk)
            return success_response({"message": "Deleted successfully"}, status.HTTP_200_OK)
        except DjangoValidationError:
            return error_response({"detail": ["Category not found."]}, status.HTTP_404_NOT_FOUND)
        except Exception:
            return error_response({"detail": ["Internal server error"]}, status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ---- helper interno para PUT/PATCH ----
    def _update(self, request, pk: int, partial: bool):
        try:
            service = CategoryService()
            # Si tenés serializer de update, validá acá:
            # serializer = CategoryUpdateSerializer(instance=service.get_category(pk), data=request.data, partial=partial)
            # if not serializer.is_valid():
            #     return error_response(_normalize_errors(serializer.errors), status.HTTP_400_BAD_REQUEST)
            # payload = serializer.validated_data

            payload = request.data  # Uso los datos crudos si aún no hay serializer de write
            updated = service.update_category(pk, payload)
            data = CategoryReadSerializer(updated).data
            return success_response(data, status.HTTP_200_OK)

        except DRFValidationError as e:
            return error_response(_normalize_errors(getattr(e, "detail", str(e))), status.HTTP_400_BAD_REQUEST)
        except DjangoValidationError as e:
            payload = getattr(e, "message_dict", getattr(e, "messages", str(e)))
            return error_response(_normalize_errors(payload), status.HTTP_400_BAD_REQUEST)
        except IntegrityError:
            return error_response({"non_field_errors": ["Integrity error."]}, status.HTTP_400_BAD_REQUEST)
        except Exception:
            return error_response({"detail": ["Internal server error"]}, status.HTTP_500_INTERNAL_SERVER_ERROR)
