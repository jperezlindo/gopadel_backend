from django.contrib import admin
from .models.tournament import Tournament

@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ('name', 'date_start', 'date_end', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'facility')
    search_fields = ('name',)
    ordering = ('-created_at',)