from django.contrib import admin
from facilities.models import Facility

@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'address', 'courts', 'is_active', 'is_deleted')
    search_fields = ('name', 'address')
    list_filter = ('is_active', 'is_deleted')
