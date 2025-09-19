# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from users.models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Yo configuro el admin de usuarios personalizados con email como login.
    - Uso autocomplete para FKs (facility, city, rol).
    - Optimizo el changelist con list_select_related y búsqueda por campos clave.
    - Habilito filter_horizontal para grupos y permisos.
    """
    model = CustomUser

    # ------- Lista -------
    list_display = (
        "id",
        "email",
        "name",
        "last_name",
        "facility",
        "city",
        "rol",
        "is_active",
        "is_staff",
        "is_superuser",
        "created_at",
    )
    list_filter = ("is_active", "is_staff", "is_superuser", "created_at")
    search_fields = ("email", "name", "last_name")
    ordering = ("-created_at", "-id")
    date_hierarchy = "created_at"
    list_per_page = 50
    save_on_top = True
    list_select_related = ("facility", "city", "rol")

    # Si tus FKs son grandes, yo habilito autocomplete
    autocomplete_fields = ("facility", "city", "rol")

    # Permite seleccionar múltiples grupos/permisos con UI cómoda
    filter_horizontal = ("groups", "user_permissions")

    # Campos de solo lectura (fechas, login)
    readonly_fields = ("last_login", "created_at", "updated_at")

    # ------- Fieldsets (edición) -------
    # Yo uso los nombres de campos reales (FKs: facility/city/rol — no *_id)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Información Personal", {"fields": ("name", "last_name", "birth_day", "avatar")}),
        ("Relaciones", {"fields": ("facility", "city", "rol")}),
        ("Permisos", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Fechas", {"fields": ("last_login", "created_at", "updated_at")}),
    )

    # ------- Fieldsets (alta) -------
    # UserAdmin espera password1/password2 en el alta
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email",
                "name",
                "last_name",
                "birth_day",
                "avatar",
                "facility",
                "city",
                "rol",
                "is_active",
                "is_staff",
                "is_superuser",
                "password1",
                "password2",
            ),
        }),
    )

    # ------- Acciones masivas -------
    actions = ("mark_active", "mark_inactive")

    def get_queryset(self, request):
        # Yo optimizo el queryset para el changelist
        qs = super().get_queryset(request)
        return qs.select_related("facility", "city", "rol").only(
            "id", "email", "name", "last_name",
            "facility__id", "facility__name",
            "city__id", "city__name",
            "rol__id", "rol__name",
            "is_active", "is_staff", "is_superuser",
            "created_at", "updated_at", "last_login",
        )

    def mark_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} usuarios activados.")
    mark_active.short_description = "Activar seleccionados"

    def mark_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} usuarios desactivados.")
    mark_inactive.short_description = "Desactivar seleccionados"
