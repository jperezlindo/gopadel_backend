# test/test_exception_handler.py
"""
Pruebas del custom_exception_handler para garantizar contrato estable con el front.

- Valido códigos mapeados:
  * Django ValidationError con code='unique' -> 409
  * Django ValidationError con code='not_found' -> 404
  * DRF ValidationError -> 400
  * IntegrityError con mensaje de unicidad -> 409
  * Exception genérica -> 500

- Uso APIRequestFactory para evitar registrar rutas. Cada vista de prueba
  declara AllowAny y sin auth para no acoplar las pruebas a JWT.
"""

import pytest
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.test import APIRequestFactory
from rest_framework import status as http


def _flatten_msgs(payload) -> str:
    """
    Mantengo este helper para normalizar el dict de errores en un string y
    poder hacer asserts simples (ideal cuando la estructura puede variar).
    """
    parts = []
    for v in payload.values():
        if isinstance(v, list):
            parts.extend([str(x) for x in v])
        else:
            parts.append(str(v))
    return " ".join(parts).lower()


@pytest.mark.django_db
class TestCustomExceptionHandler:
    def setup_method(self):
        # Preparo el factory por test para tener aislamiento
        self.factory = APIRequestFactory()

    def _call_view(self, view_cls):
        """
        Invoco una vista DRF con GET y retorno la Response resultante.
        """
        request = self.factory.get("/fake-url/")
        response = view_cls.as_view()(request)
        return response

    def test_django_validation_error_unique_maps_409(self, settings):
        """
        Quiero asegurarme de que un ValidationError con code='unique' salga como 409,
        y el payload esté normalizado (por-campo o non_field_errors).
        """
        class UniqueErrorView(APIView):
            permission_classes = [AllowAny]
            authentication_classes = []

            def get(self, _request):
                # Construyo un error por-campo con code 'unique'
                err = DjangoValidationError({"email": [DjangoValidationError("Ya existe.", code="unique")]})
                raise err

        resp = self._call_view(UniqueErrorView)
        assert resp.status_code == http.HTTP_409_CONFLICT
        # Espero formato normalizado por campo
        assert isinstance(resp.data, dict)
        assert "email" in resp.data
        assert isinstance(resp.data["email"], list)
        assert any("existe" in msg.lower() for msg in resp.data["email"])

    def test_django_validation_error_not_found_maps_404(self, settings):
        """
        Quiero asegurarme de que un ValidationError con code='not_found' salga 404.
        """
        class NotFoundErrorView(APIView):
            permission_classes = [AllowAny]
            authentication_classes = []

            def get(self, _request):
                # Error plano con code 'not_found'
                raise DjangoValidationError("No encontrado", code="not_found")

        resp = self._call_view(NotFoundErrorView)
        assert resp.status_code == http.HTTP_404_NOT_FOUND
        assert isinstance(resp.data, dict)
        flat = _flatten_msgs(resp.data)
        assert "no encontrado" in flat

    def test_drf_validation_error_maps_400_and_normalizes(self, settings):
        """
        Confirmo que DRF ValidationError sale 400 y conserva el detalle por-campo.
        """
        class DRFValidationView(APIView):
            permission_classes = [AllowAny]
            authentication_classes = []

            def get(self, _request):
                # Error por-campo típico de DRF
                raise DRFValidationError({"name": ["Este campo es requerido."]})

        resp = self._call_view(DRFValidationView)
        assert resp.status_code == http.HTTP_400_BAD_REQUEST
        assert isinstance(resp.data, dict)
        assert "name" in resp.data
        assert isinstance(resp.data["name"], list)
        assert any("requerido" in msg.lower() for msg in resp.data["name"])

    def test_integrity_error_unique_maps_409(self, settings):
        """
        Valido que un IntegrityError que huele a unicidad mapee a 409.
        """
        class IntegrityUniqueView(APIView):
            permission_classes = [AllowAny]
            authentication_classes = []

            def get(self, _request):
                # Simulo un error de unicidad de DB
                raise IntegrityError("UNIQUE constraint failed: users_customuser.email")

        resp = self._call_view(IntegrityUniqueView)
        assert resp.status_code == http.HTTP_409_CONFLICT
        assert isinstance(resp.data, dict)
        flat = _flatten_msgs(resp.data)
        assert "integridad" in flat or "unique" in flat

    def test_unhandled_exception_maps_500(self, settings):
        """
        Cierro con un caso genérico: cualquier excepción no mapeada debe dar 500 y payload estándar.
        """
        class BoomView(APIView):
            permission_classes = [AllowAny]
            authentication_classes = []

            def get(self, _request):
                raise Exception("Boom!")

        resp = self._call_view(BoomView)
        assert resp.status_code == http.HTTP_500_INTERNAL_SERVER_ERROR
        assert isinstance(resp.data, dict)
        flat = _flatten_msgs(resp.data)
        assert "error interno" in flat
