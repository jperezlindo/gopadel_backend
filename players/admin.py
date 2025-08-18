from django.contrib import admin
from .models.player import Player

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('id', 'nick_name', 'position', 'level', 'points', 'is_active', 'created_at', 'updated_at')
    list_filter = ('position', 'level')
    search_fields = ('nick_name', 'position')
    ordering = ('-created_at',)
