# categories/schemas/category_schemas.py
from rest_framework import serializers
from categories.models.category import Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "is_active")
        read_only_fields = ("id",)