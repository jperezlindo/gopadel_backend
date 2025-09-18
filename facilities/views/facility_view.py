# facilities/views/facility_view.py
# Este archivo es un puente estable para que urls.py importe desde "views"
# y no se acople al path real de los controllers.

from facilities.controllers.facility_controller import (
    FacilityListCreateView,
    FacilityDetailView,
)

__all__ = ["FacilityListCreateView", "FacilityDetailView"]
