from django.contrib import admin
from cities.models import City

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'cod', 'is_active', 'is_deleted')
    search_fields = ('name', 'cod')
    list_filter = ('is_active', 'is_deleted')