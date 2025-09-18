# test/test_pagination.py
"""
Smoke test de la paginación unificada.

Objetivo:
- Verificar que DefaultPagination entregue el contrato:
  count, page, page_size, total_pages, next, previous, results
- Validar cálculo de páginas con distintos page_size y page.
- No dependo de modelos ni DB: uso una lista en memoria.
"""

from rest_framework.test import APIRequestFactory
from rest_framework.request import Request
from utils.pagination import DefaultPagination


def _drf_request(path: str) -> Request:
    """
    Creo un Request de DRF desde el factory para que el paginator
    tenga .query_params disponible y no falle con WSGIRequest.
    """
    factory = APIRequestFactory()
    django_req = factory.get(path)
    return Request(django_req)


def test_default_pagination_first_page():
    request = _drf_request("/fake-url/?page=1&page_size=10")

    # Dataset de 0..99 (100 ítems)
    items = list(range(100))

    paginator = DefaultPagination()
    paginator.request = request
    page = paginator.paginate_queryset(items, request)
    response = paginator.get_paginated_response(page)

    data = response.data
    assert data["count"] == 100
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert data["total_pages"] == 10
    assert data["next"] is not None
    assert data["previous"] is None
    # Los primeros 10 elementos: 0..9
    assert data["results"] == list(range(10))


def test_default_pagination_middle_page_custom_size():
    request = _drf_request("/fake-url/?page=3&page_size=15")

    items = list(range(100))

    paginator = DefaultPagination()
    paginator.request = request
    page = paginator.paginate_queryset(items, request)
    response = paginator.get_paginated_response(page)

    data = response.data
    assert data["count"] == 100
    assert data["page"] == 3
    assert data["page_size"] == 15
    assert data["total_pages"] == 7  # ceil(100/15) = 7
    assert data["next"] is not None
    assert data["previous"] is not None
    # Página 3 con size 15 -> índices 30..44
    assert data["results"] == list(range(30, 45))


def test_default_pagination_last_page_and_bounds():
    # Pido un page_size enorme para verificar el límite max_page_size=200
    request = _drf_request("/fake-url/?page=1&page_size=9999")

    items = list(range(250))  # 250 elementos

    paginator = DefaultPagination()
    paginator.request = request
    page = paginator.paginate_queryset(items, request)
    response = paginator.get_paginated_response(page)

    data = response.data
    # Se respeta el límite max_page_size=200
    assert data["page_size"] == 200
    assert data["total_pages"] == 2  # ceil(250/200) = 2
    assert data["page"] == 1
    assert len(data["results"]) == 200

    # Ahora voy a la última página
    request_last = _drf_request("/fake-url/?page=2&page_size=200")
    paginator_last = DefaultPagination()
    paginator_last.request = request_last
    page_last = paginator_last.paginate_queryset(items, request_last)
    response_last = paginator_last.get_paginated_response(page_last)

    data_last = response_last.data
    assert data_last["page"] == 2
    assert data_last["previous"] is not None
    assert data_last["next"] is None
    # Últimos 50 elementos: índices 200..249
    assert data_last["results"] == list(range(200, 250))
