# categories/schemas/category_serializers.py
"""
Serializers de Categories.

Objetivo de este módulo:
- Exponer un serializer de **lectura** con contrato estable para el front.
- Mantener el conjunto de campos acotado a lo que realmente necesita la UI hoy.
- Preparar el camino para agregar serializers de escritura (Create/Update)
  sin romper el contrato de lectura que ya consume el cliente.
"""

# Importo DRF para construir serializers basados en el modelo.
from rest_framework import serializers

# Importo el modelo de dominio que voy a serializar.
from categories.models.category import Category


class CategoryReadSerializer(serializers.ModelSerializer):
    """
    Serializer de **lectura** (read-only) usado para listar y mostrar categorías.

    Decisiones:
    - Uso ModelSerializer para mapear campos 1:1 con el modelo sin lógica adicional.
    - Expongo únicamente los campos necesarios para la UI actual.
    - Marco todos los campos como read_only para dejar explícito que este serializer
      NO se usa para crear/editar (evito usos incorrectos y cambios involuntarios).
    """
    class Meta:
        # Especifico el modelo de origen para el mapeo automático de campos.
        model = Category

        # Defino explícitamente los campos expuestos al cliente.
        # Esto me da control total del contrato que consumirá el front.
        fields = ("id", "name", "is_active")

        # Aclaro que estos campos no se escriben usando este serializer.
        read_only_fields = ("id", "name", "is_active")


# Exporto explícitamente lo que quiero que se pueda importar desde este módulo.
__all__ = ["CategoryReadSerializer"]
