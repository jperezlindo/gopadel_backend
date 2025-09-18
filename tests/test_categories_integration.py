# tests/test_categories_integration.py
"""
Pruebas de integración por controller para Categories (read-only).

Objetivo:
- Validar el contrato de paginación: count, page, page_size, total_pages, next, previous, results.
- Verificar filtros (?is_active, ?search) y orden (?order_by).
- Probar el detalle existente (200) e inexistente (404 mapeado por el handler).

Decisión:
- Invoco las vistas DRF directamente con APIRequestFactory (sin depender del URLConf),
  así aislo la lógica del endpoint y evito 404 del enrutador en este entorno.
"""

import pytest
from rest_framework.test import APIRequestFactory
from categories.models.category import Category
from categories.views.category_view import CategoryListView, CategoryDetailView


@pytest.fixture
def factory():
    """Factory para construir requests hacia las vistas DRF."""
    return APIRequestFactory()


@pytest.fixture
def seed_categories(db):
    """
    Dataset simple:
    - Tres activas (Beginner, Amateur, Pro)
    - Dos inactivas (Junior, Senior)
    """
    Category.objects.create(name="Beginner", is_active=True)
    Category.objects.create(name="Amateur",  is_active=True)
    Category.objects.create(name="Pro",      is_active=True)
    Category.objects.create(name="Junior",   is_active=False)
    Category.objects.create(name="Senior",   is_active=False)


def test_list_basic_pagination(factory, seed_categories):
    # Simulo GET /api/v1/categories/?page=1&page_size=2
    request = factory.get("/api/v1/categories/?page=1&page_size=2")
    resp = CategoryListView.as_view()(request)

    assert resp.status_code == 200
    data = resp.data

    # Estructura de paginación esperada por DefaultPagination
    assert set(data.keys()) == {"count", "page", "page_size", "total_pages", "next", "previous", "results"}
    assert data["count"] == 5
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total_pages"] == 3
    assert isinstance(data["results"], list)
    assert len(data["results"]) == 2

    item = data["results"][0]
    assert set(item.keys()) == {"id", "name", "is_active"}


def test_list_filter_is_active_true(factory, seed_categories):
    request = factory.get("/api/v1/categories/?is_active=true&page_size=50")
    resp = CategoryListView.as_view()(request)

    assert resp.status_code == 200
    data = resp.data

    assert data["count"] == 3
    names = [item["name"].lower() for item in data["results"]]
    for expected in ("beginner", "amateur", "pro"):
        assert expected in names


def test_list_filter_is_active_false(factory, seed_categories):
    request = factory.get("/api/v1/categories/?is_active=false&page_size=50")
    resp = CategoryListView.as_view()(request)

    assert resp.status_code == 200
    data = resp.data

    assert data["count"] == 2
    names = [item["name"].lower() for item in data["results"]]
    for expected in ("junior", "senior"):
        assert expected in names


def test_list_search(factory, seed_categories):
    request = factory.get("/api/v1/categories/?search=or&page_size=50")
    resp = CategoryListView.as_view()(request)

    assert resp.status_code == 200
    data = resp.data

    assert data["count"] == 2
    names = sorted([item["name"].lower() for item in data["results"]])
    assert names == ["junior", "senior"]


def test_list_order_by_name(factory, seed_categories):
    request = factory.get("/api/v1/categories/?order_by=name&page_size=50")
    resp = CategoryListView.as_view()(request)

    assert resp.status_code == 200
    data = resp.data

    expected = ["Amateur", "Beginner", "Junior", "Pro", "Senior"]
    got = [item["name"] for item in data["results"]]
    assert got == expected


def test_list_order_by_invalid_field_fallback(factory, seed_categories):
    request = factory.get("/api/v1/categories/?order_by=__invalid__&page_size=50")
    resp = CategoryListView.as_view()(request)

    assert resp.status_code == 200
    data = resp.data
    assert data["count"] == 5
    # No verifico el orden exacto; alcanza con que no falle y devuelva todo.


def test_detail_ok(factory, seed_categories):
    # Tomo un PK real del seed para evitar asumir que es 1 (el autoincremento puede variar).
    pk = Category.objects.order_by("id").values_list("id", flat=True).first()
    request = factory.get(f"/api/v1/categories/{pk}/")
    resp = CategoryDetailView.as_view()(request, pk=pk)

    assert resp.status_code == 200
    data = resp.data
    assert set(data.keys()) == {"id", "name", "is_active"}
    assert data["id"] == pk
    assert isinstance(data["name"], str)


def test_detail_not_found_maps_404(factory, seed_categories):
    # Busco un ID inexistente garantizado (mayor al máximo actual)
    max_id = Category.objects.order_by("-id").values_list("id", flat=True).first()
    missing_pk = (max_id or 0) + 1000

    request = factory.get(f"/api/v1/categories/{missing_pk}/")
    resp = CategoryDetailView.as_view()(request, pk=missing_pk)

    # Nuestro custom_exception_handler mapea ValidationError(code='not_found') a 404.
    assert resp.status_code == 404
    err = resp.data
    assert isinstance(err, dict)
    assert any(k in err for k in ("detail", "non_field_errors", "name"))
