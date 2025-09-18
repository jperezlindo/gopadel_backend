# gopadel_backend/urls.py (referencia, no lo toco ahora)
from django.urls import path, include

urlpatterns = [
    # ...
    path("api/v1/categories/", include("categories.urls.category_urls")),
]
