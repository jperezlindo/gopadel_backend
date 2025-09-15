# categories/urls/category_urls.py
from django.urls import path
from categories.views.category_view import CategoryListView, CategoryDetailView

urlpatterns = [
    path("", CategoryListView.as_view(), name="category_list"),
    path("<int:pk>/", CategoryDetailView.as_view(), name="category_detail"),
]
