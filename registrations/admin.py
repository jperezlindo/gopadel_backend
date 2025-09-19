# registrations/admin.py
from django.contrib import admin
from django.db.models import QuerySet

# Yo importo explícito para evitar depender de __init__.py
from registrations.models.registration import Registration
from registrations.models.registration_unavailability import RegistrationUnavailability


class RegistrationUnavailabilityInline(admin.TabularInline):
    """
    Yo muestro y edito las indisponibilidades directamente
    dentro de la inscripción (UX más rápida en backoffice).
    """
    model = RegistrationUnavailability
    extra = 0
    fields = ("day_of_week", "start_time", "end_time", "created_at")
    readonly_fields = ("created_at",)
    ordering = ("day_of_week", "start_time")


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    """
    Yo optimizo el admin de inscripciones:
    - Columnas clave y valores “humanos” para las relaciones
    - Búsqueda por jugador/pareja/categoría/torneo
    - Filtros por estado de pago, activo y referencias relacionadas
    - Inline de indisponibilidades
    - Acciones masivas para activar/desactivar y marcar estado de pago
    """
    # ----- Lista -----
    list_display = (
        "id",
        "tournament_col",
        "tournament_category_col",
        "player_col",
        "partner_col",
        "paid_amount",
        "payment_status",
        "is_active",
        "created_at",
    )
    list_filter = (
        "is_active",
        "payment_status",
        # Yo agrego filtros por relaciones más usadas
        ("tournament_category", admin.RelatedOnlyFieldListFilter),
        ("tournament_category__tournament", admin.RelatedOnlyFieldListFilter),
    )
    search_fields = (
        # Yo busco por nombres de relaciones comunes
        "tournament_category__name",
        "tournament_category__tournament__name",
        "player__nick_name",
        "player__name",
        "partner__nick_name",
        "partner__name",
        "payment_reference",
        "id",
    )
    ordering = ("-created_at", "-id")
    date_hierarchy = "created_at"
    list_per_page = 50
    save_on_top = True

    # Yo pongo FK grandes en autocomplete para no cargar miles de opciones
    autocomplete_fields = ("tournament_category", "player", "partner")

    # Inline de indisponibilidades
    inlines = [RegistrationUnavailabilityInline]

    # Evito N+1: cargo relaciones necesarias en el changelist
    list_select_related = (
        "tournament_category",
        "tournament_category__tournament",
        "tournament_category__category",
        "player",
        "partner",
    )

    readonly_fields = ()  # si querés, podés volver read-only created_at/updated_at

    # ----- Queryset optimizado -----
    def get_queryset(self, request):
        # Yo agrego select_related a lo que ya definí arriba
        qs = super().get_queryset(request)
        return qs.select_related(
            "tournament_category",
            "tournament_category__tournament",
            "tournament_category__category",
            "player",
            "partner",
        )

    # ----- Columnas “humanas” -----
    def tournament_col(self, obj: Registration):
        t = getattr(obj.tournament_category, "tournament", None)
        if t:
            return f"[{t.id}] {getattr(t, 'name', '')}"
        return "—"
    tournament_col.short_description = "Tournament"

    def tournament_category_col(self, obj: Registration):
        tc = obj.tournament_category
        if tc:
            return f"[{tc.id}] {tc.name}"
        return "—"
    tournament_category_col.short_description = "Tournament Category"

    def player_col(self, obj: Registration):
        p = obj.player
        if p:
            nick = getattr(p, "nick_name", None) or getattr(p, "name", None)
            return f"[{p.id}] {nick}" if nick else p.id
        return "—"
    player_col.short_description = "Player"

    def partner_col(self, obj: Registration):
        p = obj.partner
        if p:
            nick = getattr(p, "nick_name", None) or getattr(p, "name", None)
            return f"[{p.id}] {nick}" if nick else p.id
        return "—"
    partner_col.short_description = "Partner"

    # ----- Acciones masivas -----
    actions = (
        "mark_active",
        "mark_inactive",
        "mark_paid",
        "mark_pending",
        "mark_refunded",
    )

    def mark_active(self, request, queryset: QuerySet[Registration]):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} inscripciones activadas.")
    mark_active.short_description = "Activar seleccionadas"

    def mark_inactive(self, request, queryset: QuerySet[Registration]):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} inscripciones desactivadas.")
    mark_inactive.short_description = "Desactivar seleccionadas"

    def _set_payment_status(self, request, queryset: QuerySet[Registration], value: str, label: str):
        updated = queryset.update(payment_status=value)
        self.message_user(request, f"{updated} inscripciones marcadas como {label}.")

    def mark_paid(self, request, queryset: QuerySet[Registration]):
        # Yo uso un valor simple y consistente; si luego definís choices, lo adapto.
        self._set_payment_status(request, queryset, value="paid", label="PAID")
    mark_paid.short_description = "Marcar pago = PAID"

    def mark_pending(self, request, queryset: QuerySet[Registration]):
        self._set_payment_status(request, queryset, value="pending", label="PENDING")
    mark_pending.short_description = "Marcar pago = PENDING"

    def mark_refunded(self, request, queryset: QuerySet[Registration]):
        self._set_payment_status(request, queryset, value="refunded", label="REFUNDED")
    mark_refunded.short_description = "Marcar pago = REFUNDED"
