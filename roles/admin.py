from django.contrib import admin
from roles.models import Rol

@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'is_active', 'is_deleted')
    search_fields = ('name',)
    list_filter = ('is_active', 'is_deleted')
