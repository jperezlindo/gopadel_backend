# utils/pagination.py
"""
Paginación unificada para toda la API.

Acá centralizo el comportamiento para no repetirlo en cada vista y para que el front
tenga siempre el mismo contrato. Se exponen metadatos útiles: page, page_size, total_pages.
Se permite ajustar page_size vía query param, con un límite superior para evitar abusos.
"""

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class DefaultPagination(PageNumberPagination):
    # Tamaño por defecto de página. Si no se especifica ?page_size=, se usa este valor.
    page_size = 20

    # Permite que el cliente defina el tamaño de página: ?page_size=50
    page_size_query_param = "page_size"

    # Límite superior del tamaño de página para evitar abusos.
    max_page_size = 200

    # Nombre del query param de página: ?page=2
    page_query_param = "page"

    def get_paginated_response(self, data):
        """
        Devuelve un contrato consistente y práctico para el front.
        Se mantiene 'results' por compatibilidad con DRF y se agregan metadatos útiles.
        """
        return Response({
            "count": self.page.paginator.count,
            "page": self.page.number,
            "page_size": self.get_page_size(self.request) or self.page_size,
            "total_pages": self.page.paginator.num_pages,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "results": data,
        })
